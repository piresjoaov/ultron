import time
from server import LlamaServer
from ui import Spinner
from config import DEVELOPMENT_MODE
from orchestration.orchestrator import Orchestrator

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
    orchestrator = Orchestrator(messages=messages)
    spinner = Spinner("Assistant: ")

    try:
        while True:
            user_input = input("User: ")

            if user_input.lower() == "exit":
                break

            start_time = time.time()
            spinner.start()

            def on_first_token(token):
                spinner.stop()
                print(token, end="", flush=True)

            response = orchestrator.handle_message(user_input, on_token=on_first_token)
            spinner.stop()
            if DEVELOPMENT_MODE:
                print("\n[Routing] "
                    f"category={response.task_category}; selected={response.model_id}; "
                    f"model_ref={response.metadata['model_ref']}; "
                    f"endpoint={response.metadata['endpoint'] or 'default'}; "
                    f"fallback={response.metadata['fallback_used']}; "
                    f"sanitized={response.metadata['output_sanitized']}; "
                    f"reason={response.routing_reason}")

            elapsed = time.time() - start_time
            print(f"\nResponse time: {elapsed:.2f} seconds\n")

    finally:
        server.stop()

if __name__ == "__main__":
    main()
