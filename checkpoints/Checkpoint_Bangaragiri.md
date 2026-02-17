# While You Were Gone (Since 2026-02-11)

## Changes Summary
The system underwent a **major architectural evolution**, shifting from a Python-specific tool to a **language-agnostic developer onboarding platform** with:
- **Universal LLM Support**: Added LiteLLM integration for OpenAI, Anthropic, Mistral, Azure, Ollama, and more.
- **Git Workflow Automation**: Auto-generates checkpoints on commit via git hooks.
- **Interactive Setup**: Wizard-driven configuration with language detection and validation.
- **Metadata-Rich Storage**: Filenames now support authorship and project tags (e.g., `Checkpoint-Jane-2026-02-17-abc123.md`).

---

## New Dependencies
| Dependency       | Purpose                                  | Impact                          |
|------------------|------------------------------------------|---------------------------------|
| `litellm`        | Multi-provider LLM abstraction           | Enables switching between LLMs  |
| `pydantic`       | Configuration modeling                   | Validates and manages settings  |
| `typer`          | CLI argument parsing                     | Powers the interactive setup    |

---

## Refactors

### 1. Git Hook Installer
**Problem**: Hooks assumed global `checkpoint` installation, blocking local development.
**Solution**:
- **Development Mode Detection**: Hooks now auto-detect `.venv/bin/python main.py` in the repo root.
- **Dynamic Command Generation**:
  ```sh
  # Dev mode (new)
  ".venv/bin/python" "main.py" --commit "$COMMIT_HASH"

  # Production (unchanged)
  checkpoint --commit "$COMMIT_HASH"
  ```
**Impact**: Developers can test changes **without global installs**.

### 2. Storage Layer
**Problem**: Hardcoded date parsing failed with new metadata-rich filenames (e.g., `Checkpoint-Jane-2026-02-17-abc123.md`).
**Solution**:
- **Regex-Based Parsing**: Extracts dates from both legacy (`YYYY-MM-DD-hash.md`) and new formats.
- **Graceful Degradation**: Skips malformed files instead of crashing.
**Impact**: Supports **incremental adoption** of new naming conventions.

### 3. Configuration System
- **Modular Design**: Pydantic models for settings (e.g., LLM provider, git hook paths).
- **Feature Toggles**: Enable/disable components like diagram generation.
- **Environment Variables**: Override config via `.env` (e.g., `OPENAI_API_KEY`).

---

## Current Focus
1. **LLM Integration Testing**:
   - Validate performance across providers (OpenAI vs. Ollama).
   - Optimize prompt templates for non-Python languages.
2. **Git Hook Robustness**:
   - Test edge cases (e.g., missing `.venv`, nested repos).
   - Add hook **conflict resolution** for existing git configs.
3. **Metadata Expansion**:
   - Extend filename parsing to support `Project-Author-Date-Hash.md`.
   - Enable queries like `"Show all checkpoints by Jane in ProjectX"`.

---
**Next Steps for You**:
- Test local dev workflow: `git commit` should now trigger `main.py` via `.venv`.
- Try the setup wizard: Run `checkpoint --setup` to configure your LLM provider.
- Review new checkpoints: Filenames now include **author/project metadata**.