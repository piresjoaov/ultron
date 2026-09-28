import os
import subprocess
import urllib.request
import time
from config import (
    SERVER_PATH, MODEL_HF, MODEL_PATH, DEVICE, LOG_FILE, HEALTH_URL, STARTUP_TIMEOUT,
    SERVER_CTX_SIZE, SERVER_GPU_LAYERS, SERVER_THREADS, SERVER_THREADS_BATCH,
    SERVER_BATCH_SIZE, SERVER_UBATCH_SIZE, SERVER_PARALLEL, SERVER_CACHE_PROMPT,
)

class LlamaServer:
    def __init__(self, startup_timeout=STARTUP_TIMEOUT):
        self.process = None
        self.startup_timeout = startup_timeout

    def start(self):
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        model_args = ["-m", MODEL_PATH] if MODEL_PATH else ["-hf", MODEL_HF]
        self.process = subprocess.Popen([
            SERVER_PATH,
            *model_args,
            "--n-gpu-layers", str(SERVER_GPU_LAYERS),
            "--device", DEVICE,
            "--flash-attn", "on",
            "--ctx-size", str(SERVER_CTX_SIZE),
            "--threads", str(SERVER_THREADS),
            "--threads-batch", str(SERVER_THREADS_BATCH),
            "--batch-size", str(SERVER_BATCH_SIZE),
            "--ubatch-size", str(SERVER_UBATCH_SIZE),
            "--parallel", str(SERVER_PARALLEL),
            "--fit", "on",
            "--log-file", LOG_FILE
        ] + (["--cache-prompt"] if SERVER_CACHE_PROMPT else []),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        deadline = time.monotonic() + self.startup_timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError(f"llama-server stopped during startup (exit code {self.process.returncode}). See {LOG_FILE}.")
            if self.is_ready():
                model_name = MODEL_PATH or MODEL_HF
                print(f"llama-server is ready (model: {model_name})!\n")
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
