# The Master Context: Repository Intelligence System

## Architectural Overview
This system is designed to reduce developer cognitive load by automatically documenting codebase evolution and providing structured onboarding paths. It operates through three primary modes:

1.  **Checkpointing**: Captures atomic changes and historical context.
2.  **Onboarding (`--onboard`)**: Generates and updates this `MASTER_CONTEXT.md` file by analyzing the file tree and historical checkpoints.
3.  **Catch-up (`--catchup`)**: Aggregates changes over a specific timeframe to summarize activity for returning developers.

### Core Components
-   **Entry Point (`main.py`)**: A CLI-based interface managing state validation and mode selection.
-   **Agent Layer (`src/agents.py`)**: Utilizes a modular LLM framework (DSPy patterns) where "Signatures" define task intent and "Modules" handle the execution of summaries and synthesis.
-   **Workflow Engine (`src/graph.py`)**: Likely uses a directed graph (e.g., LangGraph) to orchestrate the flow of data between agents and storage.
-   **Intelligence Layer (`src/llm.py` & `src/vector_db.py`)**: Manages interactions with LLM providers (specifically Google Gemini) and local vector embeddings for retrieval-augmented context.
-   **Utility Layer (`src/git_utils.py` & `src/storage.py`)**: Interfaces with the local Git environment and manages the file-based persistence of checkpoints.

---

## Key Decision Log

### 1. Documentation-as-Code (Jan 2026)
**Decision**: Integrate `MASTER_CONTEXT.md` generation directly into the automated checkpoint workflow.
**Reasoning**: Manual documentation inevitably rots. By making the high-level "Map" a generated artifact, we ensure that new developers and AI agents always have an accurate representation of the repository.

### 2. Resilience over Latency (Jan 2026)
**Decision**: Implement a 35-second synchronous sleep upon encountering `RESOURCE_EXHAUSTED` (429) errors from the Gemini API.
**Reasoning**: In automation pipelines, a delayed success is significantly better than a fast failure that breaks the CI/CD or local workflow.

### 3. Separation of Logic and Persistence (Jan 2026)
**Decision**: Purge `.chroma_db` binary files from version control and add them to `.gitignore`.
**Reasoning**: Tracking binary database files caused repository bloat and merge conflicts. The system now requires an explicit bootstrap/ingestion step, treating the vector store as a local cache rather than a source of truth.

---

## Gotchas & Tech Debt

### 1. Synchronous Rate Limiting
The 35-second sleep in `src/llm.py` is blocking. While reliable for single-user CLI runs, it will bottleneck the system if multiple agents are parallelized or if the system is moved to a multi-user web backend.

### 2. System Tool Dependency
The `get_file_tree` utility relies on the system-level `tree` or `find` commands. Windows environments or minimal Docker containers without these utilities will fail.

### 3. Date-Based File Filtering
Storage retrieval relies heavily on a `YYYY-MM-DD` naming convention for checkpoints. If a checkpoint file is renamed or the format is altered, the `catchup` and `onboard` logic may miss historical context.

---

## Dependency Map

### External Dependencies
-   **LLM Provider**: Google Generative AI (Gemini Pro).
-   **Vector DB**: ChromaDB (Local persistence).
-   **Environment**: Git CLI must be configured with a local user email.

### Internal Module Flow
1.  **CLI (`main.py`)** calls the **Workflow (`src/graph.py`)**.
2.  **Workflow** fetches context via **Git Utils** and **Storage**.
3.  **Agents (`src/agents.py`)** process the raw data using **LLM (`src/llm.py`)**.
4.  **Results** are persisted back via **Storage** and staged via **Git Utils**.