# CLAUDE.md

AI-powered checkpoint/context generator for git repositories. Uses DSPy + LangGraph + LiteLLM to analyze commits, generate onboarding docs, and create catchup summaries.

## Commands

```bash
# Install
pip install -r requirements.txt

# Run modes
python3 main.py --onboard              # Generate master context doc
python3 main.py --catchup               # Catchup for current git user
python3 main.py --catchup user@email    # Catchup for specific user
python3 main.py --catchup-all           # Catchup for all active devs
python3 main.py --commit <hash>         # Analyze a specific commit
python3 main.py --commit <hash> --dry-run  # Print instead of saving

# Setup & config
python3 main.py --init                  # Interactive setup wizard
python3 main.py --config                # Show current config
python3 main.py --install-hook          # Install git post-commit hook
python3 main.py --uninstall             # Remove git hook

# Tests
python3 -m pytest tests/
```

## Architecture

`main.py` (CLI) routes to three flows:
- **Onboard**: builds `MasterContextGenerator` DSPy agent, feeds file tree + recent checkpoints + Mermaid diagrams, outputs `MASTER_CONTEXT.md`
- **Catchup**: `CatchupGenerator` DSPy agent synthesizes checkpoints since user's last commit
- **Commit**: LangGraph state machine (`src/graph.py`): configure -> analyze -> save -> index(ChromaDB)

## Key Modules

| File | Role |
|------|------|
| `src/agents.py` | DSPy `Signature` + `ChainOfThought` modules for all LLM tasks |
| `src/graph.py` | LangGraph `StateGraph` for commit analysis pipeline |
| `src/llm.py` | LiteLLM-based config; `detect_provider_from_model()` auto-routes providers |
| `src/config.py` | Pydantic models (`CheckpointConfig`); loads from `.checkpoint.yaml` |
| `src/storage.py` | Save/list checkpoints and catchups (timestamped markdown files under `checkpoints/`) |
| `src/git_utils.py` | GitPython wrappers: diffs, commit metadata, author detection via `user.email` |
| `src/vector_db.py` | ChromaDB persistent client at `.chroma_db` for semantic search |
| `src/mermaid_utils.py` | AST-based Mermaid diagram generation (dependency graph, class hierarchy) |
| `src/llm_diagrams.py` | LLM-based diagram generation for non-Python languages |
| `src/setup.py` | Interactive setup wizard (`questionary`-based) |
| `src/git_hook_installer.py` | Post-commit hook install/uninstall |

## Configuration

- `.checkpoint.yaml` — runtime config (LLM provider/model, output paths, feature flags)
- `.env` — API keys (`MISTRAL_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.)
- Config schema: `src/config.py` Pydantic models (`LLMConfig`, `RepositoryConfig`, `FeaturesConfig`)

## Conventions

- Small functions, broad try/except with user-facing prints for error handling
- Lazy imports for heavy deps (DSPy, ChromaDB, GitPython) — setup commands stay fast
- Timestamped filenames for checkpoints and catchups
- LLM output is stripped of code fences via `strip_code_fences()` in `src/agents.py`
- LiteLLM handles provider routing; model names auto-prefixed (e.g., `mistral/mistral-medium-2508`)
