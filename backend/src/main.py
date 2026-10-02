import asyncio
import time
from server import LlamaServer
from ui import Spinner
from config import DEVELOPMENT_MODE, configure_console_encoding
from client import ChatClientError
from orchestration.orchestrator import Orchestrator

async def main():
    configure_console_encoding()
    server = LlamaServer()
    await asyncio.to_thread(server.start)

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
            user_input = await asyncio.to_thread(input, "User: ")

            if user_input.lower() == "exit":
                break

            start_time = time.monotonic()
            first_output_time = None
            last_output_time = None
            spinner.start()

            def on_first_token(token):
                nonlocal first_output_time, last_output_time
                now = time.monotonic()
                first_output_time = first_output_time or now
                last_output_time = now
                spinner.stop()

            try:
                response = await orchestrator.handle_message(user_input, on_token=on_first_token)
            except ChatClientError as exc:
                spinner.stop()
                print(f"\nError communicating with the model: {exc}\n")
                continue
            spinner.stop()
            if DEVELOPMENT_MODE:
                print("\n[Routing] "
                    f"category={response.task_category}; selected={response.model_id}; "
                    f"model_ref={response.metadata['model_ref']}; "
                    f"endpoint={response.metadata['endpoint'] or 'default'}; "
                    f"fallback={response.metadata['fallback_used']}; "
                    f"sanitized={response.metadata['output_sanitized']}; "
                    f"reason={response.routing_reason}")

            elapsed = time.monotonic() - start_time
            output_elapsed = ((last_output_time - first_output_time)
                              if first_output_time is not None else 0)
            if first_output_time is not None and output_elapsed <= 0:
                output_elapsed = elapsed
            completion_tokens = response.metadata.get("completion_tokens", 0)
            if output_elapsed > 0 and completion_tokens:
                speed = completion_tokens / output_elapsed
                estimate_suffix = " (estimated)" if response.metadata.get("token_count_estimated") else ""
                print(f"\nResponse time: {elapsed:.2f} seconds")
                print(f"Generation speed: {speed:.2f} tokens/sec{estimate_suffix}\n")
            else:
                print(f"\nResponse time: {elapsed:.2f} seconds")
                print("Generation speed: unavailable\n")

    finally:
        await asyncio.to_thread(server.stop)

if __name__ == "__main__":
    asyncio.run(main())
