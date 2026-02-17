# While You Were Gone (2026-02-11 → 2026-02-17)

## Changes Summary

### 🔧 **Storage Layer**
- **Regex-Based Date Parsing**: Replaced hardcoded string slicing with `re.compile(r'(\d{4})-(\d{2})-(\d{2})')` to support both legacy (`YYYY-MM-DD-hash.md`) and new (`Checkpoint-Author-YYYY-MM-DD-hash.md`) filename formats.
- **Impact**: Future-proofs metadata (e.g., authorship) without breaking existing checkpoints.

### 🔄 **Git Hooks**
1. **Post-Commit → Pre-Push Migration**:
   - Checkpoints now generate **only during `git push`** (not every commit), reducing local overhead.
   - Example: `git commit -m "WIP"` no longer triggers checkpoints; they’re created on `git push`.
2. **Dev Mode Support**:
   - Hooks dynamically detect local development (via `.venv/bin/python` + `main.py`) and run without global installation.

### 🤖 **LLM Integration**
- **Universal Provider Support**: Replaced Mistral-specific code with **LiteLLM**, enabling OpenAI, Anthropic, Azure, and Ollama.
- **Configuration**: Centralized in `.checkpoint.yaml` (e.g., `provider: mistral`, `model: mistral-medium-2508`).

### ⚙️ **Configuration**
- **New File**: `.checkpoint.yaml` manages:
  - LLM settings (API keys, models).
  - Git hook patterns (ignores `node_modules`, `venv`).
  - Vector DB (Chroma) and output paths (`./checkpoints`).

## New Dependencies
| Dependency      | Purpose                          |
|-----------------|----------------------------------|
| `litellm`       | Universal LLM provider interface |
| `chromadb`      | Local vector embeddings storage  |
| `pydantic`      | Configuration validation        |

## Refactors
1. **Storage Layer**:
   - **Before**: `cp.name[:10]` (fragile string slicing).
   - **After**: Regex-based parsing with graceful error handling.
2. **Git Hooks**:
   - **Before**: Global `checkpoint` command required.
   - **After**: Dynamic command generation (`".venv/bin/python main.py"` in dev mode).

## Current Focus
1. **Testing**:
   - Validate LiteLLM integrations across providers.
   - Stress-test pre-push hooks with large commit ranges.
2. **Documentation**:
   - Update setup guides for `.checkpoint.yaml`.
   - Add examples for multi-language workflows.
3. **Expansion**:
   - Add support for Go/Rust (currently Python/JS/C++/Java).
   - Explore auto-generated architectural diagrams.

---
**Action Required**:
- Uninstall old post-commit hooks: `python -m git_hook_installer uninstall`.
- Configure `.checkpoint.yaml` (set `api_key_env` for LLM access).