# While You Were Gone

## Changes Summary
Since **2026-02-17**, the Code Checkpoint system has undergone significant architectural improvements to enhance flexibility, performance, and language support:

- **Storage Layer**: Updated filename parsing to support metadata-rich formats (e.g., `Checkpoint-Jane-2026-02-17-abc123.md`) while maintaining backward compatibility.
- **Git Hooks**:
  - Migrated from **post-commit** to **pre-push** to reduce local development overhead.
  - Added **development mode** for seamless local testing without global installations.
- **LLM Integration**: Replaced Mistral-specific code with **LiteLLM**, enabling support for OpenAI, Anthropic, Azure, and others.
- **Language Support**: Expanded beyond Python to include JavaScript, C/C++, Java, Go, and Rust.

---

## New Dependencies
| Component       | Purpose                                                                 |
|-----------------|-------------------------------------------------------------------------|
| **LiteLLM**     | Universal LLM provider integration (replaces Mistral-specific code).  |
| **Chroma DB**   | Local vector database for semantic search (stored in `.chroma_db`).    |
| **Pydantic**    | Modular configuration management (e.g., `.checkpoint.yaml`).          |

---

## Refactors
1. **Storage Layer**:
   - Replaced hardcoded date parsing with regex to support flexible filename formats.
   - Added graceful error handling for malformed filenames.
2. **Git Hooks**:
   - Dynamic command generation for dev/local environments.
   - Pre-push hook logic to process commit ranges during `git push`.
3. **Configuration**:
   - Centralized settings in `.checkpoint.yaml` (LLM, DB, git hooks, ignored paths).
   - Interactive setup wizard for guided onboarding.

---

## Current Focus
- **Testing**: Validate LLM provider integrations and git hook reliability.
- **Documentation**: Update diagrams and examples for new workflows (e.g., pre-push hooks).
- **Expansion**: Add language-specific features (e.g., diagram generation for JavaScript/TypeScript).

**Action Required**:
- Uninstall legacy post-commit hooks and install pre-push hooks:
  ```bash
  python -m git_hook_installer uninstall
  python -m git_hook_installer install
  ```
- Configure `.checkpoint.yaml` for your LLM provider and repository paths.