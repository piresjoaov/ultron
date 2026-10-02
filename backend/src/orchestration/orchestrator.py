import asyncio
import inspect
import json
import re
import sys
import time

from client import ChatClientError, stream_chat_completion
from config import MAX_TOOL_ROUNDS
from models.catalog import ModelCatalog
from models.types import AssistantResponse
from tools.registry import TOOL_DEFINITIONS, TOOLS
from .model_router import ModelRouter
from .output_policy import PlainTextOutputPolicy
from .task_classifier import TaskClassifier

class Orchestrator:
    def __init__(self, messages=None, catalog=None, classifier=None, router=None, chat_client=stream_chat_completion, max_tool_rounds=MAX_TOOL_ROUNDS, output_policy=None):
        self.messages = messages if messages is not None else []
        self.catalog = catalog or ModelCatalog()
        self.classifier = classifier or TaskClassifier()
        self.router = router or ModelRouter(self.catalog)
        self.chat_client = chat_client
        self.max_tool_rounds = max_tool_rounds
        self.output_policy = output_policy or PlainTextOutputPolicy()

    async def handle_message(self, user_input, on_token=None):
        task = self.classifier.classify(user_input, self.messages)
        decision = self.router.route(task)
        model = self.catalog.get(decision.model_id)
        self.messages.append({"role": "user", "content": user_input})
        calls_made, final_text = [], ""
        completion_tokens = 0
        token_count_estimated = False
        started = time.monotonic()
        for round_number in range(self.max_tool_rounds):
            try:
                text, tool_calls, stream_usage = await self._consume_stream(model, on_token)
            except ChatClientError:
                if not model.requires_token:
                    raise
                local_models = [candidate for candidate in self.catalog.available_models()
                                if not candidate.requires_token]
                if not local_models:
                    raise
                model = local_models[0]
                decision = decision.__class__(
                    model.id, task.category,
                    "Cloud request failed; using local model fallback",
                    decision.confidence * 0.7, True)
                text, tool_calls, stream_usage = await self._consume_stream(model, on_token)
            if stream_usage is None:
                completion_tokens += max(1, round(len(text.encode("utf-8")) / 4)) if text else 0
                token_count_estimated = True
            else:
                completion_tokens += stream_usage
            final_text = text or final_text
            if not tool_calls:
                if final_text:
                    self.messages.append({"role": "assistant", "content": final_text})
                break
            self.messages.append({"role": "assistant", "content": text or None, "tool_calls": [self._tool_call_message(call, index) for index, call in enumerate(tool_calls)]})
            for index, call in enumerate(tool_calls):
                call_id = call.get("id") or f"call_{len(calls_made) + index + 1}"
                result = await asyncio.to_thread(self._execute_tool, call)
                calls_made.append({**call, "id": call_id, "result": result})
                self.messages.append({"role": "tool", "tool_call_id": call_id, "content": result})
            if round_number == self.max_tool_rounds - 1:
                suffix = "Tool calling stopped after the configured safety limit."
                final_text = f"{final_text}\n\n{suffix}" if final_text else suffix
                break
        review = self.output_policy.review(final_text)
        return AssistantResponse(review.text, decision.model_id, task.category, decision.reason, tool_calls=calls_made, metadata={"model_ref": model.model_ref, "endpoint": model.endpoint, "routing_confidence": decision.confidence, "fallback_used": decision.fallback_used, "output_sanitized": review.changed, "output_policy_violations": list(review.violations), "latency_ms": int((time.monotonic() - started) * 1000), "completion_tokens": completion_tokens, "token_count_estimated": token_count_estimated})

    async def _consume_stream(self, model, on_token):
        text_parts, calls, buffer = [], {}, ""
        in_tool_call = False
        completion_tokens = None
        stream = self.chat_client(
            self.messages, tools=TOOL_DEFINITIONS, endpoint=model.endpoint,
            model=model.model_ref, api_url=model.api_url,
            requires_token=model.requires_token, enable_thinking=False)
        if inspect.isawaitable(stream):
            stream = await stream
        async for event in stream:
            kind = event.get("kind") if isinstance(event, dict) else event.kind
            if kind == "usage":
                usage = event.get("usage") if isinstance(event, dict) else event.usage
                if usage and usage.get("completion_tokens") is not None:
                    completion_tokens = usage["completion_tokens"]
                continue
            if kind == "tool_call":
                call = event.get("tool_call") if isinstance(event, dict) else event.tool_call
                self._merge_tool_call(calls, call)
                continue
            content = event.get("content", "") if isinstance(event, dict) else event.content
            if not content:
                continue
            buffer, in_tool_call = self._consume_content(
                buffer + content, in_tool_call, calls, text_parts, on_token)
        if buffer and not in_tool_call:
            self._emit_visible(buffer, text_parts, on_token)
        return "".join(text_parts), list(calls.values()), completion_tokens

    def _consume_content(self, buffer, in_tool_call, calls, text_parts, on_token):
        opening, closing = "<tool_call>", "</tool_call>"
        while buffer:
            if in_tool_call:
                end = buffer.find(closing)
                if end < 0:
                    return buffer, True
                self._parse_markup_call(buffer[:end], calls)
                buffer, in_tool_call = buffer[end + len(closing):], False
                continue
            start = buffer.find(opening)
            if start >= 0:
                self._emit_visible(buffer[:start], text_parts, on_token)
                buffer, in_tool_call = buffer[start + len(opening):], True
                continue
            prefix_length = max((size for size in range(1, min(len(buffer), len(opening) - 1) + 1)
                                 if opening.startswith(buffer[-size:])), default=0)
            visible = buffer[:-prefix_length] if prefix_length else buffer
            self._emit_visible(visible, text_parts, on_token)
            return buffer[-prefix_length:] if prefix_length else "", False
        return "", in_tool_call

    @staticmethod
    def _emit_visible(content, text_parts, on_token):
        if not content:
            return
        # Keep streamed output subject to the same plain-text boundary as the final response.
        content = re.sub(r"\*\*|__|`", "", content)
        content = re.sub(r"</?tool_call>", "", content, flags=re.IGNORECASE)
        if not content:
            return
        text_parts.append(content)
        if on_token:
            on_token(content)
        sys.stdout.write(content)
        sys.stdout.flush()

    @staticmethod
    def _merge_tool_call(calls, call):
        if not call:
            return
        index = call.get("index", 0)
        entry = calls.setdefault(index, {"id": "", "name": None, "arguments": ""})
        entry["id"] = call.get("id") or entry["id"]
        entry["name"] = call.get("name") or entry["name"]
        entry["arguments"] += call.get("arguments", "")

    @staticmethod
    def _parse_markup_call(raw, calls):
        try:
            call = json.loads(raw.strip())
        except (json.JSONDecodeError, TypeError):
            return
        if isinstance(call, dict):
            arguments = call.get("arguments", {})
            calls[len(calls)] = {"id": call.get("id", ""), "name": call.get("name"),
                                 "arguments": json.dumps(arguments) if isinstance(arguments, dict) else arguments}

    @staticmethod
    def _tool_call_message(call, index):
        return {"id": call.get("id") or f"call_{index + 1}", "type": "function", "function": {"name": call.get("name"), "arguments": call.get("arguments", "{}")}}

    @staticmethod
    def _execute_tool(call):
        name, raw_args = call.get("name"), call.get("arguments") or "{}"
        if name not in TOOLS:
            return f"Error: unknown tool '{name}'."
        try:
            arguments = json.loads(raw_args)
            if not isinstance(arguments, dict):
                raise ValueError("arguments must be a JSON object")
        except (json.JSONDecodeError, ValueError) as exc:
            return f"Error: invalid JSON arguments for {name}: {exc}"
        try:
            return str(TOOLS[name](**arguments))
        except Exception as exc:
            return f"Error executing {name}: {exc}"
