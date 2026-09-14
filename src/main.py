import json
import time
from server import LlamaServer
from client import stream_chat_completion
from ui import Spinner
from tools.registry import TOOLS, TOOL_DEFINITIONS

def main():
    server = LlamaServer()
    server.start()

    messages = [
        {
            'role': 'system',
            'content': (
                'You are Ultron, an AI assistant running locally with access to custom system tools. '
                'You HAVE access to the local machine and web via the provided tools. '
                'When the user asks to read, search, find files, list directories, or search the web, '
                'you MUST ALWAYS call the appropriate tool instead of claiming you cannot access the system. '
                'Do not use emojis under any circumstances. '
                'Do not use Markdown bolding or asterisks (no **text** or *text*). '
                'Output clean, direct, plain text only.'
            )
        }
    ]
    spinner = Spinner("Assistant: ")

    try:
        while True:
            user_input = input("User: ")
            if user_input.lower() == "exit":
                break

            start_time = time.time()
            messages.append({'role': 'user', 'content': user_input})

            spinner.start()

            def on_first_token(token):
                spinner.stop()
                print(token, end="", flush=True)

            bot_reply, tool_call = stream_chat_completion(
                messages, 
                tools=TOOL_DEFINITIONS, 
                on_token=on_first_token
            )
            spinner.stop()

            if tool_call["name"] and tool_call["name"] in TOOLS:
                call_id = tool_call["id"] or "call_1"
                
                messages.append({
                    "role": "assistant",
                    "content": bot_reply if bot_reply else None,
                    "tool_calls": [{
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": tool_call["name"],
                            "arguments": tool_call["arguments"]
                        }
                    }]
                })

                raw_args = tool_call.get("arguments", "{}")
                try:
                    kwargs = json.loads(raw_args) if raw_args else {}
                    result = TOOLS[tool_call["name"]](**kwargs)
                except Exception as e:
                    result = f"Error executing {tool_call['name']}: {str(e)}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": str(result)
                })

                spinner.start()
                final_reply, _ = stream_chat_completion(
                    messages, 
                    tools=None, 
                    on_token=on_first_token
                )
                spinner.stop()

                if final_reply:
                    messages.append({'role': 'assistant', 'content': final_reply})

            elif bot_reply:
                messages.append({'role': 'assistant', 'content': bot_reply})

            elapsed = time.time() - start_time
            print(f"\nResponse time: {elapsed:.2f} seconds\n")

    finally:
        server.stop()

if __name__ == "__main__":
    main()