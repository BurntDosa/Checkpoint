# While You Were Gone

## Changes Summary
- **Architectural Overhaul**: Code Checkpoint evolved from a Python-specific tool to a **language-agnostic developer onboarding platform** with universal LLM support (LiteLLM) and interactive setup.
- **Git Integration**: Added **development mode** for local testing without global installation, plus automatic checkpoint generation on commit.
- **Metadata-Rich Storage**: Updated filename parsing to support authorship/project metadata (e.g., `Checkpoint-Jane-2026-02-17-abc123.md`) while maintaining backward compatibility.

## New Dependencies
| Component          | Purpose                                                                 |
|--------------------|-------------------------------------------------------------------------|
| `.checkpoint.yaml` | Configures LLM (Mistral), Chroma DB (semantic search), and git hooks.   |
| **LiteLLM**        | Replaces Mistral-specific code; supports OpenAI, Anthropic, etc.       |
| **Chroma DB**      | Local vector database for semantic search (stored in `.chroma_db`).    |
| **Git Hooks**      | Automates checkpoint generation post-commit (dev mode supported).     |

## Refactors
1. **Storage Layer**:
   - Replaced hardcoded date extraction with regex (`r'(\d{4})-(\d{2})-(\d{2})'`) to handle legacy/new filenames.
   - Skips malformed files gracefully.
2. **Git Hook Installer**:
   - Detects `.venv/bin/python` for dev mode, dynamically generating hooks.
3. **LLM Abstraction**:
   - Migrated from Mistral-specific calls to LiteLLM’s unified interface.

## Current Focus
- **Language-Agnostic Expansion**: Adding diagram generation and context recovery for Python, JavaScript, C/C++, etc.
- **Developer Onboarding**: Interactive setup wizard and `MASTER_CONTEXT.md` for centralized insights.
- **Performance**: Monitoring Chroma DB/LLM overhead in git operations.