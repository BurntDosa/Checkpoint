# While You Were Gone

### Changes Summary
- **AI-Driven Onboarding & Catch-up:** A new **Agent Layer** has been introduced. You can now use `python main.py --onboard` to generate a repository map and `python main.py --catchup` to synthesize changes since your last activity.
- **Automated Master Context:** The project now automatically generates and commits a `MASTER_CONTEXT.md` file during the checkpoint workflow. This serves as a version-controlled "source of truth" for the repository's structure and intent.
- **Improved Reliability:** The system now handles `RESOURCE_EXHAUSTED` (429) errors from the Gemini API with an autonomous 35-second sleep/retry mechanism.
- **Repository Hygiene:** The `.chroma_db/` directory and its binary files have been removed from version control and added to `.gitignore`. Local setups now require an ingestion process to populate the vector store.

### New Dependencies
- **System Utilities:** The system now relies on system-level `tree` or `find` commands to generate structural maps.
- **Git Metadata:** The tool now interfaces with local Git configurations (`user.email`) and commit history to personalize catch-up summaries.

### Refactors
- **`main.py` Entry Point:** Introduced strict state validation and null-checks following workflow execution to prevent crashes.
- **LLM Layer:** Centralized the `GeminiLM` request logic, adding a 3-attempt retry policy and simplifying configuration management.
- **Workflow Renaming:** Standardized automation steps to include context updates (e.g., "Run Checkpoint Agent & Update Master Context").

### Current Focus
- **Documentation Stability:** Ensuring the `main.py --onboard` logic remains stable, as it is now a critical path for the automated workflow.
- **Execution Performance:** Monitoring the impact of the synchronous 35-second rate-limit sleep on total execution time.
- **Environment Bootstrapping:** Establishing a standardized process for new contributors to initialize the local vector database now that binary files are no longer tracked.