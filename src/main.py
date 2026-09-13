import json
import urllib.request
import subprocess
import time
import threading
import itertools
from tools import get_time
from tools.registry import TOOLS

url = 'http://127.0.0.1:8080/v1/chat/completions'

server_path = r"C:\Users\joaov\llama.cpp\build\bin\Release\llama-server.exe"

server = subprocess.Popen([
    server_path,
    "-hf", "Qwen/Qwen3-8B-GGUF:Q4_K_M",
    "--device", "Vulkan1",
    "--flash-attn", "on",
    "--fit", "on",
    "--log-file", "logs/llama-server.log"
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

messages = [
    {'role': 'system', 'content': 'You are a helpful assistant.'}
]

bot_reply = ""

def server_is_ready():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=1) as response:
            return response.status == 200
    except:
        return False

def spinner(stop_event):
    for char in itertools.cycle("|/-\\"):
        if stop_event.is_set():
            break

        print(f"\rAssistant: {char}", end="", flush=True)
        time.sleep(0.1)

    print("\rAssistant: ", end="", flush=True)

while not server_is_ready():
    print("Waiting for llama-server...")
    time.sleep(1)

print("llama-server is ready!\n")

try:
    while True:
        message = input("User: ")

        if message.lower() == "exit":
                break

        messages.append({
            'role': 'user',
            'content': message
        })

        payload = {
            'model': 'qwen',
            'messages': messages,
            'temperature': 0.7,
            'stream': True
        }

        data = json.dumps(payload).encode('utf-8')

        headers = {
            'Content-Type': 'application/json'
        }

        req = urllib.request.Request(url, data=data, headers=headers, method='POST')

        print("Assistant: ", end="", flush=True)

        stop_spinner = threading.Event()

        spinner_thread = threading.Thread(
            target=spinner,
            args=(stop_spinner,)
        )

        spinner_thread.start()

        with urllib.request.urlopen(req) as response:
            while True:
                line = response.readline()

                if not line:
                    break

                line = line.decode('utf-8').strip()

                if not line:
                    continue

                if line.startswith("data: "):
                    line = line[6:]

                if line == "[DONE]":
                    break

                chunk = json.loads(line)

                content = chunk["choices"][0]["delta"].get("content")

                if content:
                    stop_spinner.set()
                    spinner_thread.join()
                    bot_reply += content
                    print(content, end="", flush=True)

        messages.append({
            'role': 'assistant',
            'content': bot_reply
        })

        print("\n")

finally:
    server.terminate()