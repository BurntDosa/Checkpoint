# While You Were Gone (Since 2026-01-13)

---

## Changes Summary
- **AI-Driven Onboarding**: Added `--onboard` and `--catchup` CLI commands to auto-generate repository maps and change summaries.
- **Agent Layer**: Introduced `CatchupSummarizer` and `MasterContextGenerator` to synthesize historical changes and structural context.
- **Git Integration**: Automated user activity detection (`get_last_commit_by_author`) and personalized summaries via local Git configs.
- **Storage Overhaul**: Enhanced `src/storage.py` to handle heterogeneous data (checkpoints, summaries, maps) with `YYYY-MM-DD` filtering.

---

## New Dependencies
- **System Tools**: `tree`/`find` for file structure context (used in `get_file_tree`).
- **Git Metadata**: Local user email/config now required for personalized catch-up summaries.
- **Removed**: ChromaDB binary files (`.chroma_db/`) excluded from version control; added to `.gitignore`.

---

## Refactors
- **Reliability**:
  - Added retry logic (3 attempts) and 35-second sleep for `RESOURCE_EXHAUSTED` (429) errors in `src/llm.py`.
  - Null-checks for `final_state` in `main.py` to prevent crashes.
- **Architectural Cleanup**:
  - Removed obsolete ChromaDB binaries (`chroma.sqlite3`, `*.bin` files).
  - Refactored workflow to auto-update `MASTER_CONTEXT.md` during checkpoints.

---

## Current Focus
- **Documentation-as-Code**: `MASTER_CONTEXT.md` is now version-controlled and auto-generated via `main.py --onboard`.
- **Pipeline Stability**: The `--onboard` workflow is a critical path for checkpoint automation.
- **Error Resilience**: Self-healing logic in the LLM layer reduces manual intervention.