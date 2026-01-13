# While You Were Gone

### Changes Summary
- **AI-Driven Onboarding & Catch-up:** Introduced a new "Agent Layer" that generates automated repository maps and historical change summaries. You can now use `python main.py --onboard` to create a `MASTER_CONTEXT.md` or `--catchup` to synthesize recent changes.
- **Automated Documentation Sync:** The `MASTER_CONTEXT.md` is now automatically regenerated and committed during the checkpoint workflow, ensuring documentation stays in sync with code changes.
- **Enhanced LLM Resilience:** Implemented a self-healing retry mechanism in `src/llm.py`. The system now gracefully handles `RESOURCE_EXHAUSTED` (429) errors by waiting 35 seconds before retrying.
- **Data Hygiene:** Removed `.chroma_db` binary files and SQLite databases from version control. These are now ignored via `.gitignore` to prevent repository bloat and merge conflicts.

### New Dependencies
- **System Utilities:** The system now relies on the local `tree` or `find` commands to generate file structure context.
- **Git Metadata:** Increased dependency on local Git configurations (email and commit history) for personalized summaries.
- **Environment Bootstrapping:** Since local database files were removed, new setups now require an explicit ingestion process to populate the local vector store.

### Refactors
- **CLI Entry Point (`main.py`):** Added robust state validation and null-checks for workflow outputs to prevent crashes.
- **Storage Logic (`src/storage.py`):** Enhanced retrieval logic to filter checkpoints using a `YYYY-MM-DD` naming convention.
- **Provider Layer:** Simplified configuration management in `GeminiLM` and centralized transient error recovery.

### Current Focus
- **Workflow Stability:** Ensuring the `main.py --onboard` command remains stable as it is now a critical path in the automated checkpoint pipeline.
- **Context Accuracy:** Refining the `MasterContextGenerator` to ensure high-fidelity repository maps.
- **Developer Experience:** Reducing cognitive load for new contributors through the synthesized "Master Context" document.