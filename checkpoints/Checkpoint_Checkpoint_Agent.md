# While You Were Gone

### Changes Summary
*   **AI Onboarding & Catch-up System**: Launched a new suite of tools to reduce cognitive load. You can now run `python main.py --onboard` to generate a repository map or `--catchup` to synthesize recent changes based on your last activity date.
*   **Automated Master Context**: The project now maintains a `MASTER_CONTEXT.md` file, which is automatically updated and committed during the checkpoint process. This serves as the "source of truth" for AI agents and new contributors.
*   **Resilience Layer**: Improved stability by adding a 3-attempt retry mechanism for LLM calls and specific handling for `RESOURCE_EXHAUSTED` (429) errors, including a mandatory 35-second cooldown period.
*   **Database Cleanup**: Removed `.chroma_db` binary files and SQLite databases from the repository history and added them to `.gitignore`. Local environments now require an ingestion bootstrap.

### New Dependencies
*   **System Utilities**: The system now relies on local `tree` or `find` commands to generate file tree structures.
*   **Git Metadata**: Enhanced coupling with local Git configurations (`git config user.email`) to personalize "catch-up" summaries.

### Refactors
*   **Agent Layer Implementation**: Created `src/agents.py` containing specialized modules: `CatchupGenerator`, `OnboardingSynthesizer`, and `MasterContextGenerator`.
*   **LLM Provider Logic**: Refactored `src/llm.py` to move error recovery and configuration cleanup out of the main execution flow.
*   **Input Validation**: Added strict null-checks and state verification in `main.py` following workflow invocations.

### Current Focus
*   **Stability of the Onboarding Pipeline**: Ensuring the `--onboard` command remains performant as it is now a critical path in the automated workflow.
*   **Data Lifecycle Management**: Shifting toward environment-specific bootstrap processes since local vector stores are no longer tracked.