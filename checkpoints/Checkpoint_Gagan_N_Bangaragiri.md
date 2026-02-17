# While You Were Gone (2026-02-17)

## Changes Summary
### 🔄 **Git Hook Migration**
- **What**: Checkpoint generation moved from `post-commit` → **`pre-push`** hooks.
- **Why**: Reduces overhead during local development (e.g., WIP commits no longer trigger checkpoints).
- **Impact**:
  - ✅ Faster local workflows.
  - ⚠️ Pushes may take slightly longer (checkpoints generate synchronously before push completes).
  - **Action Required**: Uninstall old hooks (`python -m git_hook_installer uninstall`) and reinstall.

### 🤖 **LLM Provider Expansion**
- **What**: Replaced Mistral-specific code with **LiteLLM** (supports OpenAI, Anthropic, Azure, Ollama, etc.).
- **Why**: Avoid vendor lock-in and enable cost/performance optimization.
- **Impact**:
  - ✅ Configure providers via `.checkpoint.yaml` (set `api_key_env`).
  - ⚠️ Requires updating API keys if migrating from Mistral.

### 📁 **Storage Layer Refactor**
- **What**: Checkpoint filenames now support **metadata-rich formats** (e.g., `Checkpoint-Jane-2026-02-17-abc123.md`).
- **Why**: Enable author/project-based queries without breaking existing files.
- **Impact**:
  - ✅ Backward-compatible (legacy `YYYY-MM-DD-hash.md` still works).
  - ✅ Future-proof for additional metadata (e.g., `ProjectX-Jane-2026-02-17-abc123.md`).

### ⚙️ **Configuration System**
- **What**: New `.checkpoint.yaml` centralizes:
  - LLM settings (provider, model, temperature).
  - Chroma DB path (`.chroma_db` for vector embeddings).
  - Git hook patterns and ignored directories.
- **Why**: Simplify setup and enable semantic search/document generation.
- **Impact**:
  - ✅ Run `python -m checkpoint setup` for an **interactive wizard**.
  - ⚠️ New directories: `checkpoints/`, `.chroma_db/`, and `MASTER_CONTEXT.md`.

---

## New Dependencies
| Component       | Purpose                          | Setup Notes                                  |
|-----------------|----------------------------------|---------------------------------------------|
| **LiteLLM**     | Multi-provider LLM abstraction   | Install via `pip install litellm`.          |
| **Chroma DB**   | Vector embeddings for search     | Auto-initialized in `.chroma_db/`.         |
| **Pydantic**    | Configuration validation         | Bundled with the package.                   |

---

## Refactors
1. **Git Hooks**:
   - **Dev Mode**: Detects local `.venv` and runs `main.py` directly (no global install needed).
   - **Error Handling**: Skips malformed filenames silently (debug logs commented out).

2. **Storage Layer**:
   - **Regex**: `r'(\d{4})-(\d{2})-(\d{2})'` extracts dates from any filename format.
   - **Performance**: Minimal overhead; I/O remains the bottleneck.

3. **Language Support**:
   - Added diagram generation and context recovery for **JavaScript, Go, Rust, C/C++**.

---

## Current Focus
1. **Upgrade Path**:
   - Run `python -m git_hook_installer uninstall` to remove old hooks.
   - Reinstall with `python -m git_hook_installer install --pre-push`.
   - Validate with `git push --dry-run`.

2. **LLM Configuration**:
   - Edit `.checkpoint.yaml` to set your preferred provider (e.g., `openai/gpt-4`).
   - Export API keys (e.g., `export OPENAI_API_KEY=xxx`).

3. **Testing**:
   - Verify checkpoint generation on `git push`.
   - Test semantic search with `python -m checkpoint search "query"`.

---
**Need Help?**
- Run `python -m checkpoint --help` for CLI options.
- Check `MASTER_CONTEXT.md` for auto-generated documentation.