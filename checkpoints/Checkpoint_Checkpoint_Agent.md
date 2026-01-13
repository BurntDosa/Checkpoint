# While You Were Gone

### Changes Summary
*   **AI Catch-up & Onboarding**: Added new CLI commands `--onboard` and `--catchup` to generate repository maps and synthesized activity summaries.
*   **Automated Documentation**: The system now automatically regenerates and commits `MASTER_CONTEXT.md` during the checkpoint process, ensuring high-level docs never drift from the implementation.
*   **Resilience Upgrades**: Implemented a self-healing mechanism in the LLM layer with a 3-attempt retry logic and a specific 35-second back-off for `RESOURCE_EXHAUSTED` errors.
*   **Git Metadata Integration**: Added utilities to retrieve local user emails and last commit dates to personalize "Catch-up" summaries.
*   **Data Cleanup**: Purged `.chroma_db` binary files and SQLite databases from the repository history to prevent bloat and merge conflicts.

### New Dependencies
*   **System Utilities**: The onboarding logic now depends on the availability of system-level `tree` or `find` commands.
*   **Environment Metadata**: Tighter coupling with local Git configuration for author detection and history filtering.
*   **Vector Store Lifecycle**: ChromaDB is now a local-only dependency; new environments require a manual bootstrap/ingestion step as data is no longer tracked in Git.

### Refactors
*   **Agent Layer Introduction**: Established `src/agents.py` containing `CatchupGenerator` and `MasterContextGenerator` to separate synthesis logic from core execution.
*   **Storage Logic**: Enhanced `src/storage.py` to handle heterogeneous data types (checkpoints vs. summaries) and filter by date-based naming conventions.
*   **CLI Validation**: Refactored `main.py` to include robust null-checks on workflow states and validated local variables for dry-run outputs.

### Current Focus
*   **Architectural Visibility**: Transitioning the project toward a "documentation-as-code" model where the LLM maintains its own context.
*   **Reliability**: Monitoring the impact of the new 35-second synchronous sleep on total execution time during high-load periods.
*   **Pipeline Stability**: Ensuring the `main.py --onboard` command remains performant, as it is now a critical path for successful workflow completion.