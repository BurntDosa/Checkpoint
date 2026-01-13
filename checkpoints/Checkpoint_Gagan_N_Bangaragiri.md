# While You Were Gone

### Changes Summary
- **AI-Driven Onboarding & Catch-up**: You can now run `python main.py --onboard` to generate a repository map and `python main.py --catchup` to see summarized changes based on your last activity date.
- **Automated Master Context**: The system now automatically maintains a `MASTER_CONTEXT.md` file. This is integrated into the checkpoint workflow, ensuring high-level documentation is always version-controlled and up-to-date.
- **Improved LLM Reliability**: The `GeminiLM` provider now handles `RESOURCE_EXHAUSTED` (429) errors gracefully with a 35-second cooldown and a 3-attempt retry mechanism.
- **Data Cleanup**: Cleaned the repository history by removing `.chroma_db` binary files and SQLite databases. Local vector stores are now excluded via `.gitignore`.

### New Dependencies
- **System Utilities**: The onboarding logic now utilizes the system-level `tree` or `find` commands to generate file structures.
- **Git Metadata**: The system now queries local Git config (`user.email`) and commit history to personalize catch-up summaries.

### Refactors
- **`main.py`**: Transitioned to a multi-mode CLI interface with enhanced state validation and null-checks for workflow outputs.
- **`src/agents.py`**: Created a dedicated Agent Layer containing `CatchupGenerator` and `MasterContextGenerator`.
- **`src/storage.py`**: Enhanced retrieval logic to filter checkpoints by `YYYY-MM-DD` naming conventions and added persistence for new document types.
- **Workflow Renaming**: Updated CI/CD steps from "Run Checkpoint Agent" to "Run Checkpoint Agent & Update Master Context".

### Current Focus
- Establishing "Documentation-as-Code" where AI agents maintain the project roadmap.
- Enhancing system autonomy through self-healing LLM request logic.
- Ensuring a clean separation between application logic and local persistence (ChromaDB).