# While You Were Gone

### Changes Summary
- **AI-Driven Catch-up & Onboarding**: Introduced two new CLI modes, `--onboard` and `--catchup`, which generate structural maps and historical summaries of the repository.
- **Automated Context Generation**: The checkpoint workflow now automatically triggers the creation of a `MASTER_CONTEXT.md` file, ensuring high-level documentation stays in sync with code changes.
- **Git Integration Enhancements**: New utilities now automatically detect user activity and local configurations to personalize summaries and automate staging of documentation artifacts.
- **Database Hygiene**: Removed `.chroma_db` binary and SQLite files from the repository and updated `.gitignore` to prevent future tracking of local persistence states.

### New Dependencies
- **System Utilities**: The system now requires access to system-level `tree` or `find` for repository mapping.
- **Git Metadata**: Tighter coupling with local Git configurations (email/author tracking) for automated context generation.
- **Master Context Artifact**: `MASTER_CONTEXT.md` is now a critical artifact for the automation pipeline.

### Refactors
- **Agent Layer Introduction**: Codebase reorganized to include `src/agents.py` with specific modules for summarization (`CatchupGenerator`) and context synthesis (`MasterContextGenerator`).
- **Storage Layer Evolution**: Enhanced `src/storage.py` to handle heterogeneous data types (checkpoints vs. synthesized summaries) and date-based filtering.
- **Workflow Renaming**: Updated CI/CD and local workflow naming conventions to reflect the dual nature of checkpoints (logging + context updates).

### Current Focus
- **Onboarding Stability**: Ensuring the `main.py --onboard` logic is robust, as it is now a critical path for successful checkpoint execution.
- **Data Lifecycle Management**: New local setups now require an explicit ingestion process since the vector database is no longer tracked in version control.
- **Context Refinement**: Monitoring the quality of the AI-synthesized "Master Context" for accuracy in representing repository intent.