# CLAUDE.md

AI-powered checkpoint/context generator for git repositories. Uses LiteLLM to analyze commits, generate onboarding docs, and create catchup summaries.

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
checkpoint --init                  # Install CI workflow + config + boilerplate MASTER_CONTEXT.md
checkpoint --config                # Show current config
checkpoint --install-hook          # Install git post-commit hook
checkpoint --uninstall             # Remove git hook

# Tests
python3 -m pytest tests/
```

## Architecture

`checkpoint_agent/__main__.py` (CLI) routes to three flows:
- **Onboard**: `MasterContextGenerator` LiteLLM agent, feeds file tree + recent checkpoints + Mermaid diagrams, outputs `MASTER_CONTEXT.md`
- **Catchup**: `CatchupGenerator` LiteLLM agent synthesizes checkpoints since user's last commit
- **Commit**: `run_pipeline()` in `checkpoint_agent/graph.py`: analyze diff -> save checkpoint

## Key Modules

| File | Role |
|------|------|
| `checkpoint_agent/agents.py` | LiteLLM-based generator classes for all LLM tasks |
| `checkpoint_agent/graph.py` | `run_pipeline()` for commit analysis (analyze + save) |
| `checkpoint_agent/llm.py` | LiteLLM-based config; `detect_provider_from_model()` auto-routes providers |
| `checkpoint_agent/config.py` | Pydantic models (`CheckpointConfig`); loads from `.checkpoint.yaml` |
| `checkpoint_agent/storage.py` | Save/list checkpoints (`checkpoints/`) and catchups (`catchups/`); per-author stable filenames |
| `checkpoint_agent/git_utils.py` | GitPython wrappers: diffs, commit metadata, author detection via `user.email` |
| `checkpoint_agent/mermaid_utils.py` | AST-based Mermaid diagram generation (dependency graph, class hierarchy) |
| `checkpoint_agent/llm_diagrams.py` | LLM-based diagram generation for non-Python languages |
| `checkpoint_agent/setup_wizard.py` | Interactive setup wizard |
| `checkpoint_agent/git_hook_installer.py` | Post-commit hook install/uninstall |
| `checkpoint_agent/templates/checkpoint.yml` | Bundled GitHub Actions workflow template |

## Configuration

- `.checkpoint.yaml` — runtime config (LLM provider/model, output paths, feature flags)
- `.env` — API keys (`MISTRAL_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.)
- Config schema: `checkpoint_agent/config.py` Pydantic models (`LLMConfig`, `RepositoryConfig`, `FeaturesConfig`)

## Folder Structure

- `checkpoints/` — per-author commit checkpoint files (`Checkpoint-AuthorName.md`), PR summaries (`PR-*.md`)
- `catchups/` — per-author catchup briefings (`Catchup_email.md`); separate from checkpoints so catchup lifecycle (create on catchup-all, delete on commit) doesn't pollute checkpoint history
- `MASTER_CONTEXT.md` — generated onboarding document (root level)

When a developer commits, their catchup file in `catchups/` is automatically deleted (they're caught up). The CI workflow uses `git add -A catchups/` to pick up both additions and deletions.

## Conventions

- Small functions, broad try/except with user-facing prints for error handling
- Lazy imports for heavy deps (GitPython, LiteLLM) — setup commands stay fast
- Per-author stable filenames for checkpoints (`Checkpoint-AuthorName.md`)
- Per-author stable filenames for catchups (`Catchup_email.md`) in `catchups/` dir
- LLM output is stripped of code fences via `strip_code_fences()` in `checkpoint_agent/agents.py`
- LiteLLM handles provider routing; model names auto-prefixed (e.g., `mistral/mistral-medium-2508`)
- SSL verification is enabled by default; set `CHECKPOINT_SSL_VERIFY=false` for corporate proxies
