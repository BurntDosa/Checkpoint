# While You Were Gone

### Changes Summary
*   **AI-Driven Contextual Tools:** Introduced `--onboard` and `--catchup` commands. The system can now generate "Master Context" documents (repository maps) and date-specific change syntheses.
*   **Automated Documentation:** The CI/CD workflow now automatically runs the onboarding agent and commits an updated `MASTER_CONTEXT.md` alongside code changes.
*   **Resilience Upgrades:** Implemented self-healing logic in the LLM layer, including a 3-attempt retry mechanism and specific handling for `RESOURCE_EXHAUSTED` (429) errors with a 35-second cooldown.
*   **Repository Hygiene:** Cleaned up the `checkpoints/` directory and removed `.chroma_db` binary/SQLite files from version control.

### New Dependencies
*   **System Tools:** The codebase now utilizes system-level `tree` or `find` utilities via `get_file_tree` to provide structural context to the LLM.
*   **Environment Metadata:** Tighter integration with local Git configurations (`user.email`) to personalize the catch-up summaries.
*   **.gitignore Update:** `.chroma_db/` is now explicitly ignored; new setups require an ingestion process to populate local vector stores.

### Refactors
*   **Agent Layer (`src/agents.py`):** Established new modules (`CatchupGenerator`, `MasterContextGenerator`) and signatures (`CatchupSummarizer`, `OnboardingSynthesizer`).
*   **Validation Gates:** `main.py` now includes strict null-checks on workflow states and `generated_markdown` keys to prevent crashes.
*   **Storage Logic:** `src/storage.py` was enhanced with `get_checkpoints_since` to filter checkpoint files using `YYYY-MM-DD` naming conventions.

### Current Focus
*   **Documentation-as-Code:** Ensuring the `MASTER_CONTEXT.md` remains a high-fidelity "source of truth" for both human developers and AI agents.
*   **Pipeline Stability:** Monitoring the `main.py --onboard` logic, as it is now a critical path for successful checkpoint commits.