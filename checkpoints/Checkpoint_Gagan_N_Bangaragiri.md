# While You Were Gone (2026-01-13 → Present)

## Changes Summary
- **CLI Expansion**: Added `--onboard` and `--catchup` commands to `main.py` for AI-driven project summaries.
- **Agent Layer**: New modules (`CatchupSummarizer`, `OnboardingSynthesizer`) synthesize repository context and changes.
- **Git Integration**: Automated user activity detection (`get_last_commit_by_author`) and context updates in workflows.
- **Storage**: Enhanced checkpoint filtering (`get_checkpoints_since`) and added persistence for `MASTER_CONTEXT.md`.

## New Dependencies
- **System Tools**: `tree`/`find` (for file tree generation).
- **Environment Coupling**: Tighter Git metadata reliance (e.g., `get_local_user_email`).

## Refactors
- **Error Handling**: Retry logic (3 attempts) and rate-limit recovery (35s sleep) in `GeminiLM.basic_request`.
- **Data Hygiene**: Removed ChromaDB binary files from version control; added `.chroma_db/` to `.gitignore`.
- **Workflow**: Renamed steps to reflect combined checkpoint + context updates (e.g., "Commit Checkpoint & Context").

## Current Focus
1. **Master Context Synchronization**: Auto-updating `MASTER_CONTEXT.md` via `--onboard` in CI/CD.
2. **Resilience**: Self-healing LLM layer and state validation in `main.py`.
3. **Repository Health**: Enforcing separation of logic/persistence (e.g., ChromaDB initialization now explicit).