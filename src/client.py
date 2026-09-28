"""Async streaming client for an OpenAI-compatible chat endpoint."""
from collections.abc import AsyncIterator
from dataclasses import dataclass
import json

import httpx

import config
from config import MAX_TOKENS, REQUEST_TIMEOUT


class ChatClientError(RuntimeError):
    """A local-model response could not be safely converted into an answer."""


@dataclass(frozen=True)
class StreamEvent:
    """One incremental item from the model stream."""

    kind: str
    content: str = ""
    tool_call: dict | None = None


async def stream_chat_completion(messages, tools=None, *, endpoint=None, api_url=None,
                                 requires_token=False, model=None,
                                 timeout=None, max_tokens=MAX_TOKENS,
                                 enable_thinking=False) -> AsyncIterator[StreamEvent]:
    """Yield visible content and structured tool-call deltas as SSE data arrives."""
    payload = {"model": model or "qwen", "messages": messages, "temperature": 0.7,
               "stream": True, "max_tokens": max_tokens,
               "chat_template_kwargs": {"enable_thinking": enable_thinking}}
    if tools:
        payload["tools"] = tools
    request_url = api_url or endpoint or config.URL
    headers = {}
    if requires_token:
        token = config.GITHUB_MODELS_TOKEN
        if not token:
            raise ChatClientError("A GitHub Models token is required for this model")
        headers["Authorization"] = f"Bearer {token}"
    try:
        async with httpx.AsyncClient(timeout=timeout or REQUEST_TIMEOUT, headers=headers) as client:
            async with client.stream("POST", request_url, json=payload) as response:
                response.raise_for_status()
                received_chunk, reasoning_chars, visible_content = False, 0, False
                async for line in response.aiter_lines():
                    decoded = line.strip()
                    if not decoded or decoded == "data: [DONE]":
                        continue
                    if decoded.startswith("data: "):
                        decoded = decoded[6:]
                    try:
                        chunk = json.loads(decoded)
                        choices = chunk.get("choices", [])
                        delta = choices[0].get("delta", {}) if choices else {}
                    except (json.JSONDecodeError, AttributeError, IndexError, TypeError) as exc:
                        raise ChatClientError(f"Malformed streaming response: {decoded[:160]!r}") from exc
                    received_chunk = True
                    content = delta.get("content")
                    if content:
                        visible_content = True
                        yield StreamEvent("content", content=content)
                    reasoning_chars += len(delta.get("reasoning_content") or "")
                    for call in delta.get("tool_calls") or []:
                        function = call.get("function") or {}
                        yield StreamEvent("tool_call", tool_call={
                            "index": call.get("index", 0), "id": call.get("id", ""),
                            "name": function.get("name"),
                            "arguments": function.get("arguments", ""),
                        })
                if not received_chunk:
                    raise ChatClientError("Chat server returned an incomplete empty stream")
                if reasoning_chars and not visible_content:
                    raise ChatClientError("Model exhausted its response budget in private reasoning; no visible answer was generated")
    except httpx.HTTPStatusError as exc:
        raise ChatClientError(f"Chat server returned HTTP {exc.response.status_code}: {exc.response.reason_phrase}") from exc
    except httpx.RequestError as exc:
        raise ChatClientError(f"Could not reach chat server: {exc}") from exc
