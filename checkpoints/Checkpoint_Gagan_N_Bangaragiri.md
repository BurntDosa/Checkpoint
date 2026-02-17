# While You Were Gone (2026-02-17 → Present)

## Changes Summary
### 🔧 **Git Hooks: Dev Mode Support**
- **Dynamic Command Generation**:
  Hooks now detect local development (via `main.py` + `.venv/bin/python`) and auto-switch to:
  ```bash
  ".venv/bin/python main.py" --commit "$COMMIT_HASH"
  ```
  *Fallback*: Uses global `checkpoint` command in non-dev environments.
- **Impact**: Eliminates global install friction for contributors.

### 🗃️ **Storage Layer: Metadata-Rich Filenames**
- **Regex-Based Parsing**:
  Supports new format `Checkpoint-Author-YYYY-MM-DD-hash.md` alongside legacy filenames.
  Example matches:
  - `Checkpoint-Jane-2026-02-17-abc123.md` → Date: `2026-02-17`
  - `2026-02-17-abc123.md` (legacy) → Date: `2026-02-17`
- **Impact**: Enables author/project-specific queries without breaking existing checkpoints.

### 🚀 **Architectural Evolution**
1. **Universal LLM Support**:
   - Replaced Mistral-specific code with **LiteLLM** (OpenAI/Anthropic/Azure/Ollama).
   - Added API key management and config validation.
2. **Git Integration**:
   - Auto-generates checkpoints on commit via hooks (with backup/restore).
3. **Language-Agnostic**:
   - Added LLM-based diagram generation + language detection (Python, JS, etc.).
4. **Packaging**:
   - Proper `pyproject.toml` + wrapper script for distribution.

## New Dependencies
| Dependency | Purpose                          | Version   |
|------------|----------------------------------|-----------|
| `litellm`  | Multi-provider LLM abstraction   | Latest    |

## Refactors
1. **`storage.py`**:
   - Replaced `cp.name[:10]` with regex `r'(\d{4})-(\d{2})-(\d{2})'` for date extraction.
   - Skips malformed filenames silently (debug logs commented out).
2. **`git_hook_installer.py`**:
   - Added `repo_root` parameter to `get_hook_template` for dev mode detection.
   - Template now uses f-strings for dynamic `checkpoint_cmd` injection.

## Current Focus
🎯 **Language-Agnostic Onboarding**:
- **Goal**: Seamless context recovery for *any* codebase (Python, JS, etc.).
- **Next Steps**:
  - Expand LLM diagram templates for non-Python languages.
  - Test git hooks in monorepos (e.g., mixed Python/TypeScript projects).
- **How You Can Help**:
  - Validate hook generation in your local env:
    ```bash
    python git_hook_installer.py --dev-mode
    ```
  - Test new filename formats with `storage.get_checkpoints_since()`.