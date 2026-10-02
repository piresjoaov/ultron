import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

import config
from orchestration.orchestrator import Orchestrator
from server import LlamaServer

config.configure_console_encoding()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    llama_server = None
    if config.AUTO_START_SERVER:
        llama_server = LlamaServer()
        if llama_server.is_ready():
            print("Using the existing llama-server on the configured health endpoint.")
        else:
            try:
                await asyncio.to_thread(llama_server.start)
            except (OSError, RuntimeError, TimeoutError) as exc:
                print(f"llama-server could not start: {exc}")
                llama_server = None
    try:
        yield
    finally:
        if llama_server:
            await asyncio.to_thread(llama_server.stop)


app = FastAPI(title="Ultron API", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws/chat")
async def chat_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    orchestrator = Orchestrator(messages=[])
    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            prompt = payload.get("content", "") if isinstance(payload, dict) else ""
            if not isinstance(prompt, str) or not prompt.strip():
                continue

            token_queue: asyncio.Queue[str | None] = asyncio.Queue()

            def on_token(token: str) -> None:
                token_queue.put_nowait(token)

            task = asyncio.create_task(orchestrator.handle_message(prompt, on_token=on_token))
            streamed = ""
            while not task.done() or not token_queue.empty():
                try:
                    token = await asyncio.wait_for(token_queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    continue
                streamed += token
                await websocket.send_json({"type": "chunk", "content": token})
            response = await task
            if not streamed and response.text:
                await websocket.send_json({"type": "chunk", "content": response.text})
            await websocket.send_json({"type": "done"})
        
    except WebSocketDisconnect:
        return
    except Exception as exc:
        await websocket.send_json({"type": "chunk", "content": f"Backend error: {exc}"})
        await websocket.send_json({"type": "done"})
