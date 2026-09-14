import json
import urllib.request
from config import URL

def stream_chat_completion(messages, tools=None, on_token=None):
    payload = {
        'model': 'qwen',
        'messages': messages,
        'temperature': 0.7,
        'stream': True,
        'max_tokens': 512
    }
    if tools:
        payload['tools'] = tools

    data = json.dumps(payload).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    req = urllib.request.Request(URL, data=data, headers=headers, method='POST')

    bot_reply = ""
    tool_call_data = {"id": "", "name": None, "arguments": ""}

    with urllib.request.urlopen(req) as response:
        while True:
            line = response.readline()
            if not line:
                break
            line = line.decode('utf-8').strip()
            if not line or line == "data: [DONE]":
                continue
            if line.startswith("data: "):
                line = line[6:]

            chunk = json.loads(line)
            delta = chunk["choices"][0]["delta"]

            content = delta.get("content")
            if content:
                bot_reply += content
                if on_token:
                    on_token(content)

            tool_calls = delta.get("tool_calls")
            if tool_calls:
                tc = tool_calls[0]
                if "id" in tc:
                    tool_call_data["id"] = tc["id"]
                fn = tc.get("function", {})
                if "name" in fn:
                    tool_call_data["name"] = fn["name"]
                if "arguments" in fn:
                    tool_call_data["arguments"] += fn["arguments"]

    return bot_reply, tool_call_data