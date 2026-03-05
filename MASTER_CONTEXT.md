# Master Context: AI-Powered Code Onboarding

**Code Checkpoint** is a system that **automates the creation of contextual onboarding documents** by analyzing Git history and generating structured Markdown checkpoints with Mermaid diagrams. Its mission is to eliminate the "cold start" problem for new engineers by providing a **searchable, visual timeline** of key changes—like a "GitHub for humans." Instead of digging through commits or relying on tribal knowledge, engineers can query checkpoints by topic (e.g., "Show me all changes to the auth system in Q2") or explore auto-generated diagrams of architectural evolution.

The system is designed around **three core principles**:
1. **Just-in-Time Documentation**: Checkpoints are generated **on-demand** (via CLI or Git hooks) when meaningful changes occur, not as an afterthought.
2. **Dual-Mode Accessibility**: Data is stored as **human-readable Markdown** (in `checkpoints/`) and **machine-queryable vectors** (in ChromaDB) to support both casual browsing and semantic search.
3. **Visual First**: Every checkpoint includes **Mermaid diagrams** (e.g., dependency graphs, class hierarchies) to help engineers grok changes spatially.

---

## Architecture Overview

### System Diagram
The codebase follows a **hexagonal architecture** with clear separation between the CLI, workflow engine, LLM agents, and storage layers. Below is the **container diagram** (from the provided Mermaid):

```mermaid
%% C4 Context + Container Diagram
flowchart TD
    %% System Context
    Developer[Developer] -->|CLI Commands| Checkpoint[Code Checkpoint\nAI Onboarding System]
    Git[Git Repository] -->|Commits| Checkpoint

    %% Containers (Hexagonal Architecture)
    subgraph Checkpoint
        direction TB
        CLI[CLI\nmain.py] --> Workflow[Workflow Engine\ngraph.py]
        Workflow --> LLM[LLM Agents\nagents.py]
        Workflow --> Storage[Storage\nstorage.py + vector_db.py]
        GitUtils[Git Integration\ngit_utils.py] --> Workflow

        %% Data Stores
        VectorDB[(VectorDB\nChromaDB)] --> Storage
        FileStorage[(Markdown Files\ncheckpoints/)] --> Storage

        %% Config
        Config[Config\nconfig.py] --> CLI
        Config --> Workflow
    end

    %% External Systems
    LLM -->|API Calls| LLMProvider[LLM Provider\nOpenAI/Mistral/etc.]
    Git -->|Hooks| Checkpoint

    %% Legend
    classDef external fill:#f96,stroke:#333,color:#000
    class Developer,Git,LLMProvider external
    classDef container fill:#bbf,stroke:#333,color:#000
    class CLI,Workflow,LLM,Storage,GitUtils container
    classDef store fill:#9f9,stroke:#333,color:#000
    class VectorDB,FileStorage store