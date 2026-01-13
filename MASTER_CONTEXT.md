# Master Context: AI-Driven Documentation & Onboarding System

## Architectural Overview
This repository is an automated intelligence layer designed to reduce developer cognitive load. It functions as a "living map" of a codebase by synthesizing Git history and file structures into human-readable summaries.

### Core Components
- **The Entry Point (`main.py`)**: A CLI-based interface supporting three primary modes: standard checkpoints, `--onboard` (generating this document), and `--catchup` (summarizing recent changes).
- **Agent Layer (`src/agents.py`)**: Contains the brains of the system. It uses `CatchupGenerator` and `MasterContextGenerator` to transform raw data (Git diffs, file trees) into structured markdown.
- **Workflow Engine (`src/graph.py`)**: Manages the state and transition between different processing nodes (e.g., fetching data -> synthesis -> storage).
- **Provider Layer (`src/llm.py`)**: A resilient wrapper around Google's Gemini API, featuring built-in retry logic and rate-limit recovery.
- **Persistence Layer (`src/storage.py` & `src/vector_db.py`)**: Handles the storage of markdown checkpoints and the indexing of repository content in ChromaDB for semantic search.

---

## Key Decision Log

### 1. Documentation-as-Code (Jan 2026)
**Decision**: Integrate `MASTER_CONTEXT.md` generation directly into the checkpoint workflow.
**Reasoning**: High-level documentation usually rots. By making the documentation update a mandatory step in the "checkpoint" process, the repo ensures that the architecture overview is never more than one commit behind the code.

### 2. Implementation of Synchronous Rate Limit Recovery
**Decision**: Implement a hard 35-second `time.sleep()` upon encountering `RESOURCE_EXHAUSTED` (429) errors from the Gemini API.
**Reasoning**: In automated pipelines, it is better to have a slow successful execution than a fast failure that requires manual re-runs.

### 3. Separation of Logic and Local Vector State
**Decision**: Removed `.chroma_db` from version control and added it to `.gitignore`.
**Reasoning**: Binary vector store files caused repository bloat and merge conflicts. The system now follows a "bootstrap on first run" model for data ingestion.

### 4. Date-Based Checkpoint Filtering
**Decision**: Enforced a `YYYY-MM-DD` naming convention for checkpoint files.
**Reasoning**: Allows the `storage.py` layer to efficiently filter and aggregate changes for the `--catchup` feature without parsing the contents of every file.

---

## Gotchas & Tech Debt

- **Rate Limit Bottleneck**: While the 35s sleep prevents crashes, it can significantly slow down the `onboard` process if the repository is large and requires multiple LLM calls.
- **System Dependency**: The `get_file_tree` utility relies on system-level `tree` or `find` commands. If running on a minimal environment (like some Docker containers), these must be manually installed.
- **State Validation**: Early versions of the graph workflow could return empty states. While `main.py` now has null-checks, the underlying `graph.py` nodes should ideally implement more robust schema validation.
- **Vector DB Bootstrap**: A new developer must run an ingestion process (indexing) before semantic features of the agents will work correctly, as the DB is no longer tracked in Git.

---

## Dependency Map

### Internal Modules
- `src.agents` -> depends on `src.llm` (for synthesis)
- `src.graph` -> orchestrates `src.agents` and `src.storage`
- `src.storage` -> interacts with `checkpoints/` and `src.vector_db`
- `src.git_utils` -> provides metadata to `src.agents`

### External Dependencies
- **Gemini API**: Primary LLM provider.
- **ChromaDB**: Vector storage for semantic context.
- **Git**: System-level Git configuration is required for `get_local_user_email`.
- **System Utils**: `tree` or `find` for generating structural maps.

Hi