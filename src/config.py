"""Runtime configuration, with environment overrides for local deployments."""
import os

def _int_env(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {value!r}") from exc

URL = os.getenv("ULTRON_API_URL", "http://127.0.0.1:8080/v1/chat/completions")
HEALTH_URL = os.getenv("ULTRON_HEALTH_URL", "http://127.0.0.1:8080/health")
SERVER_PATH = os.getenv("ULTRON_SERVER_PATH", r"C:\Users\joaov\llama.cpp\build\bin\Release\llama-server.exe")
MODEL_HF = os.getenv("ULTRON_MODEL", "Qwen/Qwen3-8B-GGUF:Q4_K_M")
DEVICE = os.getenv("ULTRON_DEVICE", "Vulkan1")
LOG_FILE = os.getenv("ULTRON_LOG_FILE", "logs/llama-server.log")
REQUEST_TIMEOUT = _int_env("ULTRON_REQUEST_TIMEOUT", 60)
STARTUP_TIMEOUT = _int_env("ULTRON_STARTUP_TIMEOUT", 120)
MAX_TOOL_ROUNDS = _int_env("ULTRON_MAX_TOOL_ROUNDS", 5)
MAX_TOKENS = _int_env("ULTRON_MAX_TOKENS", 1024)
DEVELOPMENT_MODE = os.getenv("ULTRON_DEVELOPMENT_MODE", "true").lower() in {"1", "true", "yes"}
