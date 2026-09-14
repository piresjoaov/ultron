import subprocess
import urllib.request
import time
from config import SERVER_PATH, MODEL_HF, DEVICE, LOG_FILE, HEALTH_URL

class LlamaServer:
    def __init__(self):
        self.process = None

    def start(self):
        self.process = subprocess.Popen([
            SERVER_PATH,
            "-hf", MODEL_HF,
            "-ngl", "99",
            "--device", DEVICE,
            "--flash-attn", "on",
            "-c", "8192",
            "-np", "1",
            "--fit", "on",
            "--log-file", LOG_FILE
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        while not self.is_ready():
            print("Waiting for llama-server...")
            time.sleep(1)
        print("llama-server is ready!\n")

    def is_ready(self):
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=1) as response:
                return response.status == 200
        except Exception:
            return False

    def stop(self):
        if self.process:
            self.process.terminate()