# Project Master Context: The AI Onboarding & Catch-up System

Welcome to the repository. This document serves as the high-level map for understanding the "Story" of this codebase, its architecture, and the reasoning behind its current state.

## 1. Architectural Overview
The system is designed to reduce developer cognitive load by automatically generating summaries of codebase changes and structural maps. It operates as a multi-layered pipeline:

*   **Entry Point (`main.py`)**: A multi-mode CLI supporting `--onboard` (full repo context) and `--catchup` (recent history) commands.
*   **Orchestration Layer (`src/graph.py`)**: Manages the flow of data between utilities and agents.
*   **Agent Layer (`src/agents.py`)**: The "brain" of the system. It uses structured AI modules (Signatures/Generators) to synthesize raw text into meaningful insights.
*   **Data Utilities**:
    *   `src/git_utils.py`: Extracts local developer identity and commit history.
    *   `src/storage.py`: Handles a temporal file system (YYYY-MM-DD) for checkpoints and persistence.
    *   `src/vector_db.py`: Provides semantic search capabilities (via ChromaDB) for retrieving relevant context.
*   **Storage (`/checkpoints`)**: A directory of markdown files acting as the system's "long-term memory."

## 2. Key Decision Log
*   **Transition to Agentic Synthesis**: The system moved from simple logging to using an "Agent Layer." This allows for non-linear processing—summarizing, synthesizing, and then formatting—rather than just concatenation of logs.
*   **Automated Master Context**: To solve "documentation rot," the `--onboard` command was integrated into the main automation pipeline. The `MASTER_CONTEXT.md` you are likely reading now is an automated artifact of this decision.
*   **Git-Centric Identity**: The system identifies "activity" by querying the local Git config (`user.email`). This personalizes the "Catch-up" feature to focus on what has happened since *your* last commit.
*   **Binary Exclusion**: We explicitly gitignored `.chroma_db/` and removed existing SQLite/Bin files. Decision: The vector database is treated as ephemeral/reconstructible state rather than a versioned artifact to prevent repo bloat.

## 3. Gotchas & Tech Debt
*   **System Dependencies**: The `get_file_tree` utility depends on the system having `tree` or `find` installed. If the CLI fails to generate a map, check your PATH for these utilities.
*   **Vector DB Ingestion**: Since binary database files are gitignored, a fresh clone requires a "bootstrap" or "ingestion" pass to populate the `vector_db` before semantic queries will work.
*   **Date-Based Retrieval**: `storage.py` relies on a strict `YYYY-MM-DD` naming convention for checkpoint files. Deviating from this format will cause the `get_checkpoints_since` logic to skip files.
*   **Main Pipeline Fragility**: Because `main.py --onboard` is now part of the checkpoint workflow, a failure in the LLM synthesis layer will block the commit/checkpoint process.

## 4. Dependency Map
### Internal Dependencies
*   `main.py` -> `src/graph.py` (Workflow orchestration)
*   `src/agents.py` -> `src/llm.py` (Model interaction)
*   `src/storage.py` -> `/checkpoints` (File persistence)

### External Dependencies
*   **Git CLI**: Used for metadata and commit history.
*   **ChromaDB**: Local vector storage for semantic retrieval.
*   **System `tree`**: For generating the structural map of the repository.
*   **LLM Provider**: Required for the `Synthesizer` and `Generator` modules to function.