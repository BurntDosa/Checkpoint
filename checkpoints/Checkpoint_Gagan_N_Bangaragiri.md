# While You Were Gone

## Changes Summary
- **LLM Integration**: Switched to **LiteLLM** (supports OpenAI, Mistral, Anthropic, etc.) for universal AI assistance.
- **Semantic Search**: Added **Chroma DB** for embedding-based code discovery.
- **Git Automation**: Hooks now auto-generate checkpoints on commit, with **dev mode** for local testing.
- **Language Support**: Expanded beyond Python to **JavaScript, C/C++, Java, Go, Rust**.

## New Dependencies
- **Tools**:
  - `litelLM` (multi-provider LLM abstraction).
  - `Chroma DB` (local vector database for semantic search).
- **Files**:
  - `.checkpoint.yaml` (central config for LLM, paths, and features).
  - `MASTER_CONTEXT.md` (auto-generated repository insights).

## Refactors
1. **Storage Layer**:
   - Replaced hardcoded date parsing with **regex** to support metadata-rich filenames (e.g., `Checkpoint-Jane-2026-02-17-abc123.md`).
   - Backward-compatible with legacy formats.
2. **Git Hooks**:
   - Dynamic command generation for **dev mode** (uses `.venv/bin/python main.py` instead of global `checkpoint`).
   - Cross-platform path handling.

## Current Focus
- **Onboarding**: Interactive setup wizard for new users.
- **Documentation**: Auto-generated diagrams and `README` expansions.
- **Scalability**: Testing Chroma DB performance with large repos.