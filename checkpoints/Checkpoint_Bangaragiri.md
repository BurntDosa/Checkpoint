# While You Were Gone

### Changes Summary
- **AI-Driven Documentation Agents**: Introduced a new **Agent Layer** (`src/agents.py`) featuring `CatchupSummarizer` and `OnboardingSynthesizer`. These tools allow users to generate personalized summaries of changes and structural "Master Context" maps of the repository.
- **CLI Enhancements**: Updated `main.py` with new `--onboard` and `--catchup` flags. The system now utilizes local `tree` or `find` utilities to provide structural context to the LLM.
- **Reliability Layer**: The LLM provider (`src/llm.py`) now includes a self-healing retry mechanism (3 attempts) and specific logic to handle `RESOURCE_EXHAUSTED` errors by pausing for 35 seconds.
- **Automated Context Sync**: The GitHub workflow was updated to automatically run the onboarding agent and commit the resulting `MASTER_CONTEXT.md` file whenever a checkpoint is triggered.
- **Storage Management**: Enhanced `src/storage.py` to filter checkpoints by date and added logic to clean up obsolete checkpoint files.

### New Dependencies
- **System Utilities**: The system now relies on the presence of `tree` or `find` at the OS level for directory mapping.
- **Git Metadata**: Tightened integration with local Git configurations (`user.email`) to personalize the catch-up experience.
- **Master Context Artifact**: `MASTER_CONTEXT.md` is now a required version-controlled artifact that serves as the source of truth for AI agents.

### Refactors
- **LLM Provider Logic**: Refactored `GeminiLM.basic_request` to encapsulate error handling and configuration cleanup, removing boilerplate from the caller.
- **State Validation**: Implemented strict null-checks and key validation for the `final_state` object in `main.py` to improve application stability.
- **Data Layer Purge**: Removed `.chroma_db` binary files and SQLite databases from the repository history and updated `.gitignore` to prevent future bloat.

### Current Focus
- **High-Fidelity Context**: Ensuring the stability of the `main.py --onboard` command, as it is now a critical path for the automated workflow.
- **Environment Bootstrapping**: Transitioning to a model where the vector store (ChromaDB) is populated via an ingestion process during setup rather than being pulled from version control.