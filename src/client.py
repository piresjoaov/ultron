"""Minimal streaming OpenAI-compatible HTTP client."""
import json
import socket
import urllib.error
import urllib.request
from config import MAX_TOKENS, REQUEST_TIMEOUT, URL

class ChatClientError(RuntimeError):
    """A local-model response could not be safely converted into an answer."""

def stream_chat_completion(messages, tools=None, on_token=None, *, endpoint=None, model=None,
                           timeout=None, max_tokens=MAX_TOKENS, enable_thinking=False):
    """Stream visible answer content; reasoning stays private and is never rendered."""
    payload = {"model": model or "qwen", "messages": messages, "temperature": 0.7,
               "stream": True, "max_tokens": max_tokens,
               "chat_template_kwargs": {"enable_thinking": enable_thinking}}
    if tools:
        payload["tools"] = tools
    request = urllib.request.Request(endpoint or URL, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    text, calls, received_chunk, reasoning_chars = "", {}, False, 0
    try:
        with urllib.request.urlopen(request, timeout=timeout or REQUEST_TIMEOUT) as response:
            while line := response.readline():
                try:
                    decoded = line.decode("utf-8").strip()
                except UnicodeDecodeError as exc:
                    raise ChatClientError("Server returned a non-UTF-8 streaming chunk") from exc
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
                    text += content
                    if on_token:
                        on_token(content)
                # llama.cpp returns Qwen thinking tokens here. They are deliberately
                # not printed or added to history, but tracking them prevents a blank
                # result from looking like a successful answer.
                reasoning_chars += len(delta.get("reasoning_content") or "")
                for call in delta.get("tool_calls") or []:
                    entry = calls.setdefault(call.get("index", 0), {"id": "", "name": None, "arguments": ""})
                    entry["id"] = call.get("id", entry["id"])
                    function = call.get("function") or {}
                    entry["name"] = function.get("name", entry["name"])
                    entry["arguments"] += function.get("arguments", "")
    except urllib.error.HTTPError as exc:
        raise ChatClientError(f"Chat server returned HTTP {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise ChatClientError(f"Could not reach chat server: {exc.reason}") from exc
    except socket.timeout as exc:
        raise ChatClientError("Chat request timed out") from exc
    if not received_chunk:
        raise ChatClientError("Chat server returned an incomplete empty stream")
    if not text and not calls and reasoning_chars:
        raise ChatClientError("Model exhausted its response budget in private reasoning; no visible answer was generated")
    if not text and not calls:
        raise ChatClientError("Chat server completed without visible content or tool calls")
    return text, list(calls.values())
