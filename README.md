# Ultron

A local-first, privacy-focused personal AI assistant designed to run on your own computer.

## Overview

Ultron is an experiment in building a complete local AI agent architecture from the ground up. Rather than relying on agent frameworks like LangChain, the project implements the underlying foundations: LLM inference, conversation state, streaming, tool calling, memory, and retrieval.

The long-term goal is to create a personal "command-driven workspace" that understands natural language, interacts with your files and applications through controlled tools, manages information locally, and eventually provides voice, visual, and system-level capabilities.

### Core Philosophy

**The LLM should never have unrestricted access to your computer.** Computer interaction happens through explicit, capability-based tools with validation, permissions, and sandboxing. This makes the system more predictable, secure, debuggable, and modular.

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
- **Local inference:** llama.cpp
- **Model:** Qwen3 8B (GGUF format)
- **GPU:** Vulkan on AMD Radeon RX 7700S
- **API:** OpenAI-compatible local endpoint

## Implemented Features

✅ Local LLM inference through llama.cpp  
✅ OpenAI-compatible local API communication  
✅ Streaming model responses  
✅ Conversation history and contextual responses  
✅ Local server startup and health checking  
✅ Tool registry for deterministic function execution  
✅ Tool definitions exposed to the LLM  
✅ Streaming tool-call detection and argument accumulation  
✅ First tool implementation: `get_time`  
✅ Response timing and statistics  
✅ Terminal-based interaction  
✅ Spinner/status feedback during generation  

## Tool System Design

The tool system creates a controlled boundary between model reasoning and real-world actions:

1. **LLM requests a capability** through a defined tool
2. **Python orchestrator receives** the tool call
3. **Validation and permissions** are checked
4. **Tool executes** in a sandboxed/controlled environment
5. **Result is returned** to the LLM for reasoning

This ensures predictability, auditability, and security.

## Development Roadmap

### Immediate (In Progress)
- Complete the tool-calling loop: User → LLM → Tool Call → Python Tool → Tool Result → LLM → Final Response

### Short Term (Next)
Filesystem tools for code understanding:
- `list_directory` — browse file structure
- `search_project` — find patterns and references
- `read_file` — inspect source code

These enable the workflow: **Discover → Search → Read → Understand → Modify → Test → Correct**

### Medium Term
- File modification through controlled write tools
- Project-wide code search and understanding
- Running tests and build commands
- Git-aware development workflows
- Persistent conversation history (SQLite)
- Full-text search and retrieval-augmented generation (RAG)

### Long Term
- Semantic/vector memory
- Model routing (task complexity, latency, quality, specialization)
- Multiple local models
- Web search and external information retrieval
- Sandboxed code execution
- Voice input and output
- Tauri-based graphical interface
- Calendar, tasks, documents, and PDFs
- Visual generation
- Controlled OS automation
- Mobile companion

## Getting Started

*(Instructions for installation, running locally, and basic usage will be added as the project matures.)*

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
