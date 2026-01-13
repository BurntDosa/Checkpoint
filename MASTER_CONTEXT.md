# Master Context: AI-Driven Onboarding & Catch-up System

## Architectural Overview
This repository serves as an automated documentation and context-management engine. It is designed to ingest repository state and historical changes to generate high-level summaries for developers.

### Core Components:
1.  **Entry Point (`main.py`)**: A CLI interface supporting three primary modes:
    *   **Checkpoint**: Logging current changes.
    *   **Onboard (`--onboard`)**: Generating the "Master Context" map of the repository.
    *   **Catch-up (`--catchup`)**: Summarizing recent activity based on Git history and checkpoint logs.
2.  **Agent Layer (`src/agents.py`)**: Contains the "brain" of the system. It uses specific signatures (e.g., `CatchupSummarizer`, `OnboardingSynthesizer`) to transform raw data into structured Markdown.
3.  **Workflow Orchestration (`src/graph.py`)**: Likely utilizes a graph-based state machine to manage the flow between data retrieval, LLM synthesis, and file persistence.
4.  **LLM Provider (`src/llm.py`)**: Interfaces with the Gemini API. It includes custom logic for self-healing and rate-limit management.
5.  **Storage & Vector DB (`src/storage.py`, `src/vector_db.py`)**: Manages the persistence of checkpoint files and provides semantic search capabilities (via ChromaDB), though the vector store is now kept local-only and not tracked in Git.

## Key Decision Log
*   **Documentation-as-Code Integration**: The decision was made to trigger `--onboard` automatically during the checkpoint process. This ensures that `MASTER_CONTEXT.md` is always a "living document" synced with the latest commit.
*   **Gemini Rate Limit Resilience**: To handle `RESOURCE_EXHAUSTED` (429) errors from the Gemini API, a synchronous 35-second sleep mechanism was implemented. This prioritizes task completion over execution speed.
*   **Separation of Data and Logic**: Binary files from `.chroma_db/` were explicitly removed from version control and added to `.gitignore`. This forces a clean separation between the application code and the transient local cache of the vector store.
*   **Date-Based Checkpoint Filtering**: The system uses a strict `YYYY-MM-DD` naming convention for checkpoint files to allow the `storage.py` layer to efficiently filter history without parsing every file's content.

## Gotchas & Tech Debt
*   **System Tool Dependency**: The onboarding logic relies on system-level utilities (`tree` or `find`). If these are missing from the developer's environment, the file tree generation will fail.
*   **Synchronous Delay**: The 35-second retry sleep in `src/llm.py` is blocking. In a high-concurrency environment, this would cause significant bottlenecks.
*   **State Validation**: While `main.py` now includes null-checks for workflow states, the system is sensitive to the structure of the `final_state` object. Adding a key that the agents don't expect can cause silent failures in documentation generation.
*   **Git Config Dependency**: The catch-up feature requires a local Git identity (`user.email`) to be configured to correctly identify and filter the "last activity" of the current user.

## Dependency Map
### External Dependencies
*   **Gemini API**: Primary LLM provider for synthesis.
*   **ChromaDB**: Used for vector embeddings and semantic search (local persistence).
*   **Git**: Required for metadata extraction and automation hooks.

### Internal Module Flow
*   `main.py` -> `src/graph.py` (Orchestrator)
*   `src/graph.py` -> `src/agents.py` (Logic)
*   `src/agents.py` -> `src/llm.py` (Provider)
*   `src/graph.py` -> `src/storage.py` (Persistence)
*   `src/storage.py` -> `checkpoints/*.md` (Data Source)