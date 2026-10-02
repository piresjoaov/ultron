# Ultron

A local-first, privacy-focused personal AI assistant designed to run on your own computer.

## Overview

Ultron is an experiment in building a complete local AI agent architecture from the ground up. Rather than relying on agent frameworks like LangChain, the project implements the underlying foundations of multi-turn conversations, tool calling, and information management from first principles.

The long-term goal is to create a personal "command-driven workspace" that understands natural language, interacts with your files and applications through controlled tools, manages information locally, and operates entirely within your control.

### Core Philosophy

**The LLM should never have unrestricted access to your computer.** Computer interaction happens through explicit, capability-based tools with validation, permissions, and sandboxing. This makes the system predictable, auditable, and secure.

## Current Architecture

```
User
  ↓
Python orchestrator
  ↓
Local llama.cpp server
  ↓
Local Qwen3 LLM
  ↓
Tool calling
  ↓
Python tool registry
  ↓
Deterministic tool execution
  ↓
Tool result
  ↓
LLM
  ↓
Final response
```

**Stack:**
- **Orchestration:** Python
- **Desktop UI:** Tauri v2 + Angular 18 standalone + Tailwind CSS
- **Local inference:** llama.cpp
- **Model:** Qwen3 8B (GGUF format, Q4_K_M quantization)
- **GPU:** Vulkan on AMD Radeon RX 7700S
- **API:** OpenAI-compatible local endpoint
- **Context window:** 8192 tokens

## Implemented Features

✅ Local LLM inference through llama.cpp  
✅ OpenAI-compatible local API communication  
✅ Streaming model responses  
✅ Conversation history and contextual responses  
✅ Local server startup and health checking  
✅ Tool registry for deterministic function execution  
✅ Tool definitions exposed to the LLM  
✅ Streaming tool-call detection and argument accumulation  
✅ Multi-turn conversation with tool integration  
✅ Response timing and statistics  
✅ Terminal-based interactive interface  
✅ Spinner/status feedback during generation  

## Tool System

The tool system creates a controlled boundary between model reasoning and real-world actions:

1. **LLM requests a capability** through a defined tool
2. **Python orchestrator receives** the tool call
3. **Validation and permissions** are checked
4. **Tool executes** in a sandboxed/controlled environment
5. **Result is returned** to the LLM for reasoning

This ensures predictability, auditability, and security.

### Current Tools (5 Implemented)

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_time` | Returns the current local time | None |
| `find_files` | Search for files by name in home directory tree | `query` (required), `directory`, `extension` |
| `read_file_text` | Read text content from files (.txt, .md, .py, etc) | `file_path` (required), `max_lines` |
| `list_directory` | List files and folders in a directory | `directory` (optional, defaults to Downloads) |
| `web_search` | Perform web search and return results | `query` (required), `max_results` |

## Development Roadmap

### Completed ✅
- Tool calling loop: User → LLM → Tool Call → Python Tool → Tool Result → LLM → Final Response
- File system tools (list, search, read)
- Web search capability
- Multi-turn conversation management
- Streaming response support

### Immediate (Next)
- File modification tools (write, append, create)
- Directory creation/management
- Advanced search with regex patterns
- Error handling and tool validation

### Short Term
- Execution tools (run scripts, commands)
- Git integration (status, log, diff)
- Project-aware code search
- Memory/context optimization

### Medium Term
- Persistent conversation history (SQLite)
- Full-text search and retrieval-augmented generation (RAG)
- Multi-file code understanding
- Development workflow tools

### Long Term
- Semantic/vector memory
- Model routing (task complexity, latency, quality, specialization)
- Multiple local models
- Voice input and output
- Tauri-based graphical interface
- Calendar, tasks, documents, and PDFs
- Visual generation
- Controlled OS automation
- Mobile companion

## Getting Started

### Prerequisites
- Windows (paths configured for Windows)
- llama.cpp built and compiled
- Python 3.8+
- Qwen3 8B model in GGUF format

### Installation

1. Clone the repository
2. Update paths in `backend/src/config.py`:
   - `SERVER_PATH`: Path to your llama-server.exe
   - `MODEL_HF`: Your model identifier
  - `ULTRON_MODEL_DRAFT_PATH`: Optional local draft `.gguf`; if missing, the server starts without speculative decoding
   - `DEVICE`: Your GPU device (Vulkan1, CUDA, Metal, etc)

3. Install backend dependencies:
```bash
pip install -r backend/requirements.txt
```

4. Run the terminal client:
```bash
cd backend/src
python main.py
```

5. Install the root development runner and start both services with one command:
```bash
npm install
npm run dev
```

This starts the FastAPI WebSocket backend and the Tauri/Angular desktop app together. The equivalent individual frontend command is:
```bash
cd frontend
npm install
npm run tauri:dev
```

The Angular client connects to the FastAPI WebSocket adapter at `ws://localhost:8000/ws/chat`.

### Microsoft Outlook integration

Ultron can authenticate to the configured UW-Madison Microsoft Entra tenant and
read, search, list, and move Outlook messages. It uses MSAL public-client
interactive browser authentication and caches tokens under the user's local
application-data directory. No client secret is required.

Set these environment variables in the local `.env` file (never commit that
file):

```text
MICROSOFT_CLIENT_ID=
MICROSOFT_TENANT_ID=
```

Install the backend dependencies with:

```powershell
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

To perform the first interactive login and verify `/me` and `/me/messages`
without printing an access token:

```powershell
$env:PYTHONPATH = "backend\src"
backend\.venv\Scripts\python.exe -m integrations.microsoft.verify
```

The registered Outlook tools are `authenticate_microsoft`, `list_emails`,
`read_email`, `search_emails`, and `move_email`. Ultron does not register
message sending or deletion operations.

To create a local production app and a desktop shortcut on Windows:
```powershell
npm run prod:build
```

This places `Ultron.lnk` and the production files in `Área de Trabalho\Ultron`. It also creates MSI and NSIS installers under `frontend/src-tauri/target/release/bundle/` for future distribution. Use `npm run dev` for development, then rerun `npm run prod:build` whenever you want to publish the latest confirmed implementation locally.

For a manual low-latency server launch on Windows, run `backend/scripts/start-llama-server.ps1`. It enables Flash Attention, q8_0 KV cache quantization, 99 GPU layers, and uses `ULTRON_MODEL_DRAFT_PATH` when the draft file exists.

### Usage

Once running, interact naturally:
```
User: What time is it?
User: Find my notes file
User: Read my config.py file
User: List my Downloads folder
User: Search for Python async best practices
User: exit
```

The assistant will automatically use the appropriate tools when needed.

## Project Goals

This is **not simply a chatbot**. Ultron is an experiment in building a **complete local AI agent architecture** with:

- **Privacy:** Everything runs locally on your machine
- **Security:** Explicit, sandboxed tool execution
- **Transparency:** You understand how it works
- **Modularity:** Each component can be tested and improved independently
- **Extensibility:** Easy to add new tools and capabilities

The vision is a private personal computing environment where **natural language serves as the primary interface** for information, software development, automation, and computer interaction.

## License

MIT License — See LICENSE file for details

## Author

[piresjoaov](https://github.com/piresjoaov)
