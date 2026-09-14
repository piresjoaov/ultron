import os

URL = "http://127.0.0.1:8080/v1/chat/completions"
HEALTH_URL = "http://127.0.0.1:8080/health"
SERVER_PATH = r"C:\Users\joaov\llama.cpp\build\bin\Release\llama-server.exe"
MODEL_HF = "Qwen/Qwen3-8B-GGUF:Q4_K_M"
DEVICE = "Vulkan1"
LOG_FILE = "logs/llama-server.log"