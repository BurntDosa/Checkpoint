# While You Were Gone — Since 2026-02-11
The checkpoint_agent system has undergone a deliberate **architectural simplification**, removing ChromaDB vector database integration to reduce complexity and maintenance overhead. This change eliminates semantic search capabilities but preserves the core workflow of generating and storing human-readable checkpoints. Users relying on vector search must migrate to filesystem-based alternatives, while all others benefit from faster execution, fewer dependencies, and improved reliability.

---

## Critical Changes (Must-Read)
### 🚨 **Breaking: ChromaDB Integration Removed**
1. **Configuration Failures**:
   - Any existing config files with `vector_db: true` or `vector_db_path` fields will **fail validation**. Remove these keys entirely.
   - Example: Delete these lines from `config.py` or YAML configs:
     ```yaml
     features:
       vector_db: true  # ← REMOVE
     repository:
       vector_db_path: ".chroma_db"  # ← REMOVE
     ```

2. **API/Functionality Removed**:
   - **Deleted `vector_db.py`**: The entire `VectorDB` class (with `add_checkpoint()` and `search()` methods) is gone. Code calling these will raise `ImportError`.
   - **Search Capabilities**: Semantic search is no longer available. Replace with filesystem tools like:
     ```bash
     rg "search term" checkpoints/  # ripgrep example
     ```

3. **Orphaned Data**:
   - Delete the `.chroma_db` directory (if it exists) to clean up unused storage:
     ```bash
     rm -rf .chroma_db
     ```

4. **Dependency Conflict**:
   - `chromadb>=0.4.0` was removed from `pyproject.toml` and `requirements.txt`. Update your environment:
     ```bash
     pip uninstall chromadb -y
     ```

---

## New Features & Additions
*None in this update.* This release focuses on **removal and simplification** rather than adding capabilities.

---

## Refactors & Structural Changes
### 1. **Simplified Workflow Graph** (`checkpoint_agent/graph.py`)
- **Before**: `configure → analyze → save → index → END` (parallel indexing)
- **After**: `configure → analyze → save → END` (linear, no background tasks)
- **Impact**: Faster execution, no silent failures from indexing.

### 2. **Configuration Models** (`checkpoint_agent/config.py`)
- Removed:
  - `vector_db_path` from `RepositoryConfig`
  - `vector_db` toggle from `FeaturesConfig`
- Simplified `ignore_patterns` to focus on core file filtering.

### 3. **Testing Infrastructure**
- Removed VectorDB mocks and indexing assertions.
- Tests now validate **only** checkpoint generation and filesystem storage.

### 4. **User Interfaces** (`setup_wizard.py`)
- Setup output no longer mentions vector DB.
- Configuration display is cleaner, with fewer optional features.

---

## New Dependencies & Config Changes
### **Dependencies Removed**
| Package    | Version   | Action               |
|------------|-----------|----------------------|
| `chromadb` | `>=0.4.0` | **REMOVED**           |

### **Configuration Changes**
| Key               | Old Value       | New Value       |
|-------------------|-----------------|-----------------|
| `features.vector_db` | `true/false`    | **DELETED**     |
| `repository.vector_db_path` | `".chroma_db"` | **DELETED**     |

---

## Current Focus Areas
1. **Migration Support**:
   - Team is prioritizing documentation for users affected by the ChromaDB removal (e.g., search workflow alternatives).
   - Example: A `MIGRATION.md` guide is in draft [#42](https://github.com/your-repo/checkpoint_agent/pull/42).

2. **Performance Optimization**:
   - Profiling the simplified workflow to identify further bottlenecks (e.g., large repo analysis).
   - Early results show **~20% faster** checkpoint generation without indexing overhead.

3. **Core Feature Enhancements**:
   - **In Flight**: PR [#45](https://github.com/your-repo/checkpoint_agent/pull/45) adds **checkpoint diffing** to highlight changes between versions.
   - **Planned**: Native support for **structured metadata** (e.g., JSON sidecars) alongside Markdown files.

4. **Developer Experience**:
   - Simplifying the setup wizard further to reduce cognitive load for new users.
   - Exploring **interactive tutorials** for common workflows (e.g., "How to search checkpoints without ChromaDB").

---
### **Action Items for You**
| Priority | Task                                                                 |
|----------|----------------------------------------------------------------------|
| ⭐ **Critical** | Update configs to remove `vector_db` keys.                          |
| ⭐ **Critical** | Delete `.chroma_db` directories and uninstall `chromadb`.          |
| 🔧 **High**     | Replace semantic search with `rg`/`grep` in your scripts.           |
| 📚 **Medium**   | Review the [draft migration guide](https://github.com/your-repo/checkpoint_agent/pull/42). |