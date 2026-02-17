# While You Were Gone

## Changes Summary
### 🔄 **Git Hook Overhaul**
- **Migration**: Switched from `post-commit` to **`pre-push` hooks** to reduce local overhead. Checkpoints now generate only on `git push`, ensuring they align with shared changes.
- **Development Mode**: Hooks now detect local `.venv` environments and run `main.py` directly, eliminating global installation requirements.
- **CI/CD Integration**: GitHub Actions (`checkpoint.yml`) now handles checkpoint generation for pushed commits, replacing local hooks by default.

### 🤖 **LLM & AI Infrastructure**
- **Universal LLM Support**: Replaced Mistral-specific code with **[LiteLLM](https://litellm.ai/)** to support **OpenAI, Anthropic, Azure, Ollama**, and more via a single interface.
- **Semantic Search**: Added **Chroma DB** for local vector embeddings (stored in `.chroma_db/`), enabling context-aware queries.
- **Automated Diagrams**: LLM-generated architecture diagrams (e.g., Mermaid) for onboarding.

### 📂 **Storage & Metadata**
- **Filename Flexibility**: Updated `storage.py` to parse dates from **new formats** (e.g., `Checkpoint-Jane-2026-02-17-abc123.md`) using regex, while maintaining backward compatibility.
- **Graceful Degradation**: Skips malformed files silently; no forced migration of legacy checkpoints.

### 🛠 **Configuration**
- **Centralized `.checkpoint.yaml`**:
  ```yaml
  LLM:
    provider: litellm  # Supports OpenAI/Mistral/Anthropic
    model: mistral-medium-2508
  DB:
    path: .chroma_db   # Local vector store
  Git:
    install_hook: false # Defaults to CI/CD
  ```
- **Interactive Setup**: New wizard detects languages (Python/JS/Go/Rust), validates API keys, and generates `MASTER_CONTEXT.md`.

---

## New Dependencies
| Dependency       | Purpose                          | Impact                          |
|------------------|----------------------------------|---------------------------------|
| **LiteLLM**      | Multi-provider LLM abstraction   | Enables provider switching      |
| **Chroma DB**    | Local vector embeddings          | Powers semantic search          |
| **Pydantic**     | Configuration management         | Validates `.checkpoint.yaml`    |
| **GitHub Actions**| CI/CD checkpoint generation     | Replaces local hooks by default |

---

## Refactors
1. **Git Hook Installer** (`git_hook_installer.py`):
   - Added `repo_root` parameter to auto-detect development environments.
   - Dynamic command generation for `.venv`-based execution.
2. **Storage Layer** (`storage.py`):
   - Regex-based date parsing (`r'(\d{4})-(\d{2})-(\d{2})'`) for flexible filename formats.
   - Error handling for unparseable filenames.
3. **CLI** (`main.py`):
   - New `--commit <hash>` argument for granular checkpoint generation (replaces `--onboard`).

---

## Current Focus
### 🚀 **Immediate Priorities**
- **CI/CD Migration**: Ensure teams [uninstall old hooks](https://github.com/your-repo#migration) and enable GitHub Actions.
- **LLM Provider Testing**: Validate **LiteLLM** integrations (e.g., fallbacks for rate limits).
- **Documentation**: Update README with:
  - New setup wizard flow.
  - GitHub Actions workflow examples.
  - Multi-language support guides.

### 🔮 **Upcoming**
- **Language-Specific Plugins**: Deepen support for JavaScript/Go (e.g., `tsconfig.json` parsing).
- **Performance**: Optimize Chroma DB indexing for large repos.
- **Collaboration**: Team-specific checkpoint queries (e.g., `checkpoint list --author=Jane`).

---
> **Action Required**: Run `python -m git_hook_installer uninstall` to remove legacy hooks, then configure `.checkpoint.yaml` for your LLM provider.