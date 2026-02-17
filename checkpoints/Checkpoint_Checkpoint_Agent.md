# While You Were Gone

## Changes Summary
- **Git Hooks**:
  - Migrated from `post-commit` to **`pre-push`** to reduce local overhead (checkpoints now generate only on `git push`).
  - Added **development mode** support: hooks now run `main.py` directly in local repos (no global install needed).
- **Storage Layer**:
  - Filenames now support **metadata** (e.g., `Checkpoint-Jane-2026-02-17-abc123.md`) via regex parsing.
  - Backward-compatible with legacy formats.
- **LLM Integration**:
  - Switched from Mistral to **LiteLLM** for multi-provider support (OpenAI, Anthropic, etc.).
- **CI/CD**:
  - Checkpoints are now generated in **GitHub Actions** (not locally), ensuring consistency.

## New Dependencies
- **LiteLLM**: Universal LLM interface (replaces Mistral-specific code).
- **Chroma DB**: Local vector database for semantic search (stored in `.chroma_db`).
- **GitHub Actions**: Workflow (`checkpoint.yml`) for automated checkpoint generation on push.

## Refactors
1. **`storage.py`**:
   - Replaced hardcoded date slicing with regex to parse `YYYY-MM-DD` from filenames.
   - Skips malformed files gracefully.
2. **`git_hook_installer.py`**:
   - Detects `.venv` and `main.py` to enable dev mode.
   - Generates dynamic hook commands (e.g., `".venv/bin/python main.py --commit $HASH"`).
3. **Configuration**:
   - Added `.checkpoint.yaml` for centralized settings (LLM, DB, git hooks).
   - Interactive setup wizard for language detection and validation.

## Current Focus
- **Testing**: Validate LLM providers and git hook reliability.
- **Documentation**: Update diagrams for new workflows (e.g., pre-push hooks, CI/CD integration).
- **Expansion**: Add support for more languages (beyond Python/JS) and LLM providers.