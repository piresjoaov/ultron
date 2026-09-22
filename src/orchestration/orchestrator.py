import json
import time

from client import stream_chat_completion
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

    def handle_message(self, user_input, on_token=None):
        task = self.classifier.classify(user_input, self.messages)
        decision = self.router.route(task)
        model = self.catalog.get(decision.model_id)
        self.messages.append({"role": "user", "content": user_input})
        calls_made, final_text = [], ""
        started = time.monotonic()
        for round_number in range(self.max_tool_rounds):
            # Qwen's private thinking stream can spend the entire output budget before
            # it emits an answer. Keep the terminal assistant deterministic today;
            # a future model profile may opt into bounded thinking explicitly.
            text, tool_calls = self.chat_client(
                self.messages, tools=TOOL_DEFINITIONS, on_token=None,
                endpoint=model.endpoint, model=model.model_ref, enable_thinking=False)
            final_text = text or final_text
            if not tool_calls:
                if final_text:
                    self.messages.append({"role": "assistant", "content": final_text})
                break
            self.messages.append({"role": "assistant", "content": text or None, "tool_calls": [self._tool_call_message(call, index) for index, call in enumerate(tool_calls)]})
            for index, call in enumerate(tool_calls):
                call_id = call.get("id") or f"call_{len(calls_made) + index + 1}"
                result = self._execute_tool(call)
                calls_made.append({**call, "id": call_id, "result": result})
                self.messages.append({"role": "tool", "tool_call_id": call_id, "content": result})
            if round_number == self.max_tool_rounds - 1:
                suffix = "Tool calling stopped after the configured safety limit."
                final_text = f"{final_text}\n\n{suffix}" if final_text else suffix
                break
        review = self.output_policy.review(final_text)
        if on_token and review.text:
            on_token(review.text)
        return AssistantResponse(review.text, decision.model_id, task.category, decision.reason, tool_calls=calls_made, metadata={"model_ref": model.model_ref, "endpoint": model.endpoint, "routing_confidence": decision.confidence, "fallback_used": decision.fallback_used, "output_sanitized": review.changed, "output_policy_violations": list(review.violations), "latency_ms": int((time.monotonic() - started) * 1000)})

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
