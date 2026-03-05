# CLAUDE.md

AI-powered checkpoint/context generator for git repositories. Uses DSPy + LangGraph + LiteLLM to analyze commits, generate onboarding docs, and create catchup summaries.

## Commands

```bash
# Install (for development)
pip install -e .

# Or install from PyPI (for other repos)
pip install checkpoint-agent

# Run modes
checkpoint --onboard              # Generate master context doc
checkpoint --catchup               # Catchup for current git user
checkpoint --catchup user@email    # Catchup for specific user
checkpoint --catchup-all           # Catchup for all active devs
checkpoint --commit <hash>         # Analyze a specific commit
checkpoint --commit <hash> --dry-run  # Print instead of saving

# Setup & config
checkpoint --init                  # Interactive setup wizard
checkpoint --install-ci            # Install GitHub Actions workflow
checkpoint --config                # Show current config
checkpoint --install-hook          # Install git post-commit hook
checkpoint --uninstall             # Remove git hook

# Tests
python3 -m pytest tests/
```

## Architecture

`checkpoint_agent/__main__.py` (CLI) routes to three flows:
- **Onboard**: builds `MasterContextGenerator` DSPy agent, feeds file tree + recent checkpoints + Mermaid diagrams, outputs `MASTER_CONTEXT.md`
- **Catchup**: `CatchupGenerator` DSPy agent synthesizes checkpoints since user's last commit
- **Commit**: LangGraph state machine (`checkpoint_agent/graph.py`): configure -> analyze -> save -> index(ChromaDB)

## Key Modules

| File | Role |
|------|------|
| `checkpoint_agent/agents.py` | DSPy `Signature` + `ChainOfThought` modules for all LLM tasks |
| `checkpoint_agent/graph.py` | LangGraph `StateGraph` for commit analysis pipeline |
| `checkpoint_agent/llm.py` | LiteLLM-based config; `detect_provider_from_model()` auto-routes providers |
| `checkpoint_agent/config.py` | Pydantic models (`CheckpointConfig`); loads from `.checkpoint.yaml` |
| `checkpoint_agent/storage.py` | Save/list checkpoints and catchups (timestamped markdown files under `checkpoints/`) |
| `checkpoint_agent/git_utils.py` | GitPython wrappers: diffs, commit metadata, author detection via `user.email` |
| `checkpoint_agent/vector_db.py` | ChromaDB persistent client at `.chroma_db` for semantic search |
| `checkpoint_agent/mermaid_utils.py` | AST-based Mermaid diagram generation (dependency graph, class hierarchy) |
| `checkpoint_agent/llm_diagrams.py` | LLM-based diagram generation for non-Python languages |
| `checkpoint_agent/setup_wizard.py` | Interactive setup wizard (`questionary`-based) |
| `checkpoint_agent/git_hook_installer.py` | Post-commit hook install/uninstall |
| `checkpoint_agent/templates/checkpoint.yml` | Bundled GitHub Actions workflow template |

## Configuration

- `.checkpoint.yaml` — runtime config (LLM provider/model, output paths, feature flags)
- `.env` — API keys (`MISTRAL_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.)
- Config schema: `checkpoint_agent/config.py` Pydantic models (`LLMConfig`, `RepositoryConfig`, `FeaturesConfig`)

## Conventions

- Small functions, broad try/except with user-facing prints for error handling
- Lazy imports for heavy deps (DSPy, ChromaDB, GitPython) — setup commands stay fast
- Timestamped filenames for checkpoints and catchups
- LLM output is stripped of code fences via `strip_code_fences()` in `checkpoint_agent/agents.py`
- LiteLLM handles provider routing; model names auto-prefixed (e.g., `mistral/mistral-medium-2508`)
