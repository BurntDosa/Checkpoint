# While You Were Gone (2026-02-11 → 2026-02-17)

## Changes Summary
The **Code Checkpoint** system has evolved into a **language-agnostic developer onboarding platform** with **git automation** and **multi-LLM support**. Key changes since your last activity:

| Area               | Impact                                                                 |
|--------------------|------------------------------------------------------------------------|
| **Git Hooks**      | Now supports **local development** (no global install needed).       |
| **Storage**        | Handles new filename formats (e.g., `Checkpoint-Author-Date-hash.md`).|
| **LLM Integration**| Replaced Mistral with **LiteLLM** (OpenAI, Anthropic, Azure, etc.).    |
| **Setup**          | Added **interactive wizard** and `pyproject.toml` packaging.           |
| **Language Support**| Expanded beyond Python (auto-detects language for diagrams/context).  |

---

## New Dependencies
1. **LiteLLM** (`litellm`)
   - Purpose: Universal LLM provider abstraction.
   - Action: Install via `pip install litellm` or configure API keys in the new setup wizard.
   - [Docs](https://docs.litellm.ai/).

---
## Refactors
### 1. Git Hook Installer (`git_hook_installer.py`)
- **Dev Mode Detection**:
  - Hooks now auto-detect virtual environments (`.venv/bin/python`) and execute `main.py` directly.
  - Fallback: Uses global `checkpoint` command if not in dev mode.
- **Dynamic Template**:
  - Generated hooks use f-strings to inject the correct command (dev vs. global).

### 2. Storage Layer (`storage.py`)
- **Filename Parsing**:
  - Regex-based date extraction supports **legacy** (`YYYY-MM-DD-hash.md`) and **new** formats (`Checkpoint-Author-YYYY-MM-DD-hash.md`).
  - Skips malformed files silently (no breaking changes).

---
## Current Focus
### 1. **Language-Agnostic Onboarding**
   - **Goal**: Generate context/diagrams for **any language** (not just Python).
   - **Status**:
     - LLM-based diagram generation is live.
     - Language detection integrated into the setup wizard.
   - **Next Steps**:
     - Test with non-Python repos (e.g., JavaScript, Go).
     - Provide feedback on diagram accuracy via `#dev-onboarding`.

### 2. **Git Hook Reliability**
   - **Goal**: Ensure hooks work seamlessly in **all environments** (local, CI, global).
   - **Status**:
     - Dev mode detection tested for `.venv` and `venv` paths.
     - Backup/restore functionality added for hook failures.
   - **Next Steps**:
     - Verify hook behavior in **Windows** (path separator differences).
     - Report issues to `#git-integration`.

### 3. **Multi-LLM Configuration**
   - **Goal**: Simplify provider switching (e.g., OpenAI → Ollama).
   - **Status**:
     - LiteLLM configured via `config.yaml` or env vars (e.g., `OPENAI_API_KEY`).
     - Fallback to Mistral if no key is provided.
   - **Next Steps**:
     - Update `README.md` with provider-specific examples.
     - Benchmark response quality across LLMs.

---
### How to Catch Up
1. **Re-run Setup**:
   ```bash
   python -m checkpoint setup
   ```
   - Follow the interactive wizard to configure **LLM providers** and **git hooks**.

2. **Test New Features**:
   - Commit code in a non-Python repo to trigger **language-agnostic diagrams**.
   - Check `.checkpoint.log` for hook execution details.

3. **Review**:
   - [Architecture Diagram](https://github.com/your-repo/docs/architecture)
   - [LiteLLM Configuration Guide](https://github.com/your-repo/docs/llm-setup)