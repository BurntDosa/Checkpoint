# While You Were Gone (2026-02-11 → Present)

## Changes Summary
- **Git Hooks**: Now support **development mode**—no global `checkpoint` install needed. Hooks dynamically detect `.venv` and `main.py` to run locally.
- **Storage Layer**: Updated to handle new checkpoint filenames (e.g., `Checkpoint-Jane-2026-02-17-abc123.md`) while maintaining backward compatibility.
- **System Overhaul**:
  - **Universal LLM Support**: Added `LiteLLM` integration (OpenAI, Anthropic, Mistral, etc.).
  - **Git Automation**: Hooks auto-generate checkpoints on commit.
  - **Language-Agnostic**: Works with any programming language (not just Python).
  - **Interactive Setup**: New wizard for configuration and environment detection.

## New Dependencies
| Dependency   | Purpose                          |
|--------------|----------------------------------|
| `LiteLLM`    | Multi-provider LLM support       |
| `Pydantic`   | Configuration management         |

## Refactors
1. **`storage.py`**:
   - Replaced hardcoded date parsing with regex to support metadata-rich filenames.
   - Skips malformed files gracefully.
2. **`git_hook_installer.py`**:
   - Added `repo_root` parameter for dev mode detection.
   - Dynamic command generation for local vs. global execution.

## Current Focus
- **Goal**: Position `checkpoint` as a **universal developer onboarding tool**.
- **Key Initiatives**:
  - Expand LLM provider integrations (e.g., Azure, Ollama).
  - Enhance git hook reliability (backup/restore, cross-platform testing).
  - Improve documentation with auto-generated diagrams.
- **How to Catch Up**:
  - Run `checkpoint --setup` to configure the new interactive wizard.
  - Test git hooks locally: `git commit -m "test"` → auto-generates a checkpoint.