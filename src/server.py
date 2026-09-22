import os
import subprocess
import urllib.request
import time
from config import SERVER_PATH, MODEL_HF, DEVICE, LOG_FILE, HEALTH_URL, STARTUP_TIMEOUT

class LlamaServer:
    def __init__(self, startup_timeout=STARTUP_TIMEOUT):
        self.process = None
        self.startup_timeout = startup_timeout

    def start(self):
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
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

        deadline = time.monotonic() + self.startup_timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError(f"llama-server stopped during startup (exit code {self.process.returncode}). See {LOG_FILE}.")
            if self.is_ready():
                print(f"llama-server is ready (model: {MODEL_HF})!\n")
                return
            print("Waiting for llama-server...")
            time.sleep(1)
        self.stop()
        raise TimeoutError(f"llama-server did not become healthy within {self.startup_timeout} seconds at {HEALTH_URL}")

    def is_ready(self):
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=1) as response:
                return response.status == 200
        except Exception:
            return False

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
