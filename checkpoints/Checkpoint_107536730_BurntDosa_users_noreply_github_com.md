# While You Were Gone — Since 2026-03-06

The `checkpoint_agent` system has undergone a **major architectural simplification** with the **removal of ChromaDB vector database integration**. This eliminates semantic search capabilities but reduces dependencies, improves reliability, and sharpens the focus on core checkpoint generation. If you relied on vector search, you’ll need to migrate to filesystem-based alternatives (e.g., `grep`, `ripgrep`). Other changes are largely internal refactors with minimal user impact.

---

## Critical Changes (Must-Read)

### 1. **ChromaDB Vector Search Removed (Breaking Change)**
   - The **entire semantic search feature** has been deleted, including:
     - The `vector_db.py` module (31 lines removed).
     - ChromaDB client integration, collection management, and indexing logic.
     - Configuration fields: `vector_db_path` (from `RepositoryConfig`) and `vector_db` toggle (from `FeaturesConfig`).
   - **Impact**:
     - **Existing configs with `vector_db: true` will fail validation**.
     - **`.chroma_db` directories are now orphaned** and can be safely deleted.
     - **No replacement** is provided; use filesystem tools (`grep`, `find`, or `ripgrep`) for search instead.
   - **Action Required**:
     1. Remove `vector_db` references from your config files.
     2. Delete any `.chroma_db` directories in your repo.
     3. Update dependency specs to remove `chromadb>=0.4.0`.

### 2. **Workflow Graph Simplified**
   - The workflow is now **linear**: `configure → analyze → save → END`.
   - Removed:
     - The "index" node and all ChromaDB-related imports.
     - `ThreadPoolExecutor` for background indexing (no more silent failures).
   - **Impact**: Faster execution, fewer failure points, but no parallel indexing.

### 3. **Dependency Cleanup**
   - `chromadb` removed from `pyproject.toml` and `requirements.txt`.
   - **Action Required**: Run `pip uninstall chromadb` if no longer needed, or update your dependency locks.

---

## New Features & Additions
**None**. This update focuses on **removing** optional functionality to simplify the system. The core value proposition (generating and storing human-readable checkpoints) remains unchanged.

---

## Refactors & Structural Changes

### 1. **Configuration Models (`checkpoint_agent/config.py`)**
   - Removed:
     - `vector_db_path` field from `RepositoryConfig`.
     - `vector_db` boolean from `FeaturesConfig`.
   - Simplified default ignore patterns.

### 2. **User Interfaces (`setup_wizard.py`)**
   - Vector DB no longer appears in:
     - The enabled features list during setup.
     - Configuration display outputs.
   - Confirmation messages now reflect the simplified feature set.

### 3. **Testing Infrastructure**
   - Removed VectorDB mocking from workflow tests.
   - Simplified assertions to exclude indexing verification.

### 4. **Data Flow Changes**
   - **Storage**: Checkpoints are now **only** stored as Markdown files (no secondary vector DB).
   - **Retrieval**: Revert to filesystem operations (e.g., `grep "keyword" checkpoints/*.md`).
   - **Metadata**: All context remains in file format (no embedded vectors).

---

## New Dependencies & Config Changes
| **Type**       | **Change**                          | **Action Required**                          |
|----------------|-------------------------------------|---------------------------------------------|
| **Removed**    | `chromadb>=0.4.0` dependency        | Update `requirements.txt`/`pyproject.toml`. |
| **Config**     | `vector_db` fields deleted          | Remove from configs; validation will fail otherwise. |
| **Directory**  | `.chroma_db/` orphaned              | Safe to delete.                            |

---

## Current Focus Areas

1. **Core Reliability**:
   - The team is prioritizing **stability** and **predictability** in the checkpoint generation pipeline.
   - Goal: Reduce "moving parts" to minimize failure modes.

2. **Performance**:
   - With ChromaDB indexing removed, workflow execution is **faster** and more resource-efficient.
   - Future optimizations may target Markdown generation speed.

3. **User Experience**:
   - Simplifying setup and configuration to **reduce cognitive load** for new users.
   - Exploring **better filesystem search integrations** (e.g., pre-configured `ripgrep` patterns).

4. **In-Flight PRs/Features**:
   - No major features are currently in development, but expect:
     - Improved error handling for Git operations.
     - Enhanced Markdown templating for checkpoints.

---

### Migration Checklist
1. **Immediate Actions**:
   - [ ] Remove `vector_db` from configs.
   - [ ] Delete `.chroma_db/` directories.
   - [ ] Update dependencies (`pip uninstall chromadb`).
2. **Search Alternatives**:
   - Use `ripgrep` (e.g., `rg "keyword" checkpoints/`) or `find` + `grep`.
   - Consider scripting a wrapper for common queries.
3. **Monitor**:
   - Watch for future updates on filesystem search tooling.