# While You Were Gone (2026-02-11 → 2026-02-17)

## Changes Summary
### 🔄 **Git Hook Overhaul**
- **Migration**: Hooks moved from `post-commit` to **`pre-push`** (checkpoints now generated only on `git push`).
- **Dev Mode**: Local testing no longer requires global installation—hooks auto-detect `.venv` and run `main.py` directly.
- **Action Required**: Uninstall old hooks (`python -m git_hook_installer uninstall`) and install new ones.

### 🤖 **LLM Integration**
- **Universal Support**: Replaced Mistral-specific code with **LiteLLM** (now supports OpenAI, Anthropic, Azure, Ollama, etc.).
- **Configuration**: Centralized in `.checkpoint.yaml` (set `api_key_env` for your provider).

### 📦 **CI/CD-Centric Workflow**
- **GitHub Actions**: Checkpoints now generated in CI/CD (via `checkpoint.yml`) instead of locally.
- **Granularity**: Per-commit processing (`--commit <hash>`) replaces bulk `--onboard` updates.

### 🗃️ **Storage Layer**
- **Metadata-Rich Filenames**: New format (`Checkpoint-Author-YYYY-MM-DD-hash.md`) supports authorship/project tags.
- **Backward Compatibility**: Regex parsing handles both legacy and new formats.

---

## New Dependencies
| Component       | Purpose                          | Setup Instructions                     |
|-----------------|----------------------------------|----------------------------------------|
| **LiteLLM**     | Universal LLM provider interface | `pip install litellm`                   |
| **Chroma DB**   | Vector embeddings for search      | Auto-initialized in `.chroma_db/`      |
| **GitHub Actions** | CI/CD checkpoint generation   | Enable workflow in `.github/checkpoint.yml` |

---

## Refactors
1. **`storage.py`**:
   - Replaced hardcoded date slicing with regex (`r'(\d{4})-(\d{2})-(\d{2})'`).
   - Skips malformed filenames gracefully.
2. **`git_hook_installer.py`**:
   - Dynamic command generation for dev mode (`.venv/bin/python main.py`).
   - Cross-platform path handling.

---

## Current Focus
### 🚀 **Next Steps**
- **Testing**: Validate LiteLLM integrations and pre-push hook reliability.
- **Documentation**: Update diagrams for new CI/CD workflows.
- **Expansion**: Add language-specific features (e.g., JavaScript/TypeScript support).

### ⚠️ **Breaking Changes**
- Local checkpoints **no longer auto-generate** on commit (only on push).
- Legacy `post-commit` hooks **must be uninstalled** to avoid conflicts.

### 💡 **Pro Tip**
Run `python -m git_hook_installer uninstall` to clean up old hooks before installing the new `pre-push` version.