"""Runtime configuration, with environment overrides for local deployments."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPOSITORY_ROOT / ".env")


def configure_console_encoding() -> None:
    """Use UTF-8 for backend console output when the stream supports it."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")


def _int_env(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {value!r}") from exc

# --- Local Engine Configuration ---
URL = os.getenv("ULTRON_API_URL", "http://127.0.0.1:8080/v1/chat/completions")
HEALTH_URL = os.getenv("ULTRON_HEALTH_URL", "http://127.0.0.1:8080/health")
SERVER_PATH = os.getenv("ULTRON_SERVER_PATH", r"C:\Users\joaov\llama.cpp\build\bin\Release\llama-server.exe")
MODEL_HF = os.getenv("ULTRON_MODEL", "Qwen/Qwen3-8B-GGUF:Q4_K_M")
LOCAL_MODEL_PATH = REPOSITORY_ROOT / "models" / "qwen3-8b-q4_k_m.gguf"
MODEL_PATH = os.getenv("ULTRON_MODEL_PATH") or (str(LOCAL_MODEL_PATH) if LOCAL_MODEL_PATH.is_file() else None)
MODEL_DRAFT_PATH = os.getenv(
    "ULTRON_MODEL_DRAFT_PATH",
    str(REPOSITORY_ROOT / "models" / "qwen3-0.6b-q4_k_m.gguf"),
)
DEVICE = os.getenv("ULTRON_DEVICE", "Vulkan0")
LOG_FILE = os.getenv("ULTRON_LOG_FILE", "logs/llama-server.log")
SERVER_CTX_SIZE = _int_env("ULTRON_SERVER_CTX_SIZE", 8192)
SERVER_GPU_LAYERS = _int_env("ULTRON_SERVER_GPU_LAYERS", 99)
SERVER_THREADS = _int_env("ULTRON_SERVER_THREADS", max(1, (os.cpu_count() or 8) // 2))
SERVER_THREADS_BATCH = _int_env("ULTRON_SERVER_THREADS_BATCH", os.cpu_count() or 8)
SERVER_BATCH_SIZE = _int_env("ULTRON_SERVER_BATCH_SIZE", 512)
SERVER_UBATCH_SIZE = _int_env("ULTRON_SERVER_UBATCH_SIZE", 256)
SERVER_PARALLEL = _int_env("ULTRON_SERVER_PARALLEL", 1)
SERVER_CACHE_PROMPT = os.getenv("ULTRON_SERVER_CACHE_PROMPT", "true").lower() in {"1", "true", "yes"}
SERVER_CACHE_TYPE_K = os.getenv("ULTRON_SERVER_CACHE_TYPE_K", "q8_0")
SERVER_CACHE_TYPE_V = os.getenv("ULTRON_SERVER_CACHE_TYPE_V", "q8_0")

# --- Cloud Fallback Configuration (GitHub Models) ---
GITHUB_MODELS_TOKEN = os.getenv("GITHUB_MODELS_TOKEN")
# Usando a URL oficial da Azure/GitHub Models compatível com OpenAI
GITHUB_MODELS_URL = os.getenv("GITHUB_MODELS_URL", "https://models.inference.ai.azure.com/chat/completions")

# --- Orchestration Limits ---
REQUEST_TIMEOUT = _int_env("ULTRON_REQUEST_TIMEOUT", 60)
STARTUP_TIMEOUT = _int_env("ULTRON_STARTUP_TIMEOUT", 120)
AUTO_START_SERVER = os.getenv("ULTRON_AUTO_START_SERVER", "true").lower() in {"1", "true", "yes"}
MAX_TOOL_ROUNDS = _int_env("ULTRON_MAX_TOOL_ROUNDS", 5)
MAX_TOKENS = _int_env("ULTRON_MAX_TOKENS", 1024)
DEVELOPMENT_MODE = os.getenv("ULTRON_DEVELOPMENT_MODE", "true").lower() in {"1", "true", "yes"}

# --- Canvas Configuration ---
CANVAS_API_TOKEN = os.getenv("CANVAS_API_TOKEN")
CANVAS_API_URL = os.getenv("CANVAS_API_URL", "https://canvas.wisc.edu/api/v1")

# --- Microsoft Graph Configuration ---
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID")
MICROSOFT_GRAPH_BASE_URL = os.getenv(
    "MICROSOFT_GRAPH_BASE_URL", "https://graph.microsoft.com/v1.0"
)
MICROSOFT_CACHE_PATH = os.getenv(
    "MICROSOFT_CACHE_PATH",
    str(Path.home() / "AppData" / "Local" / "Ultron" / "msal_token_cache.bin"),
)