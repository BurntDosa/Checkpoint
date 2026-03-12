# Code Checkpoint

**Code Checkpoint** is an AI-powered developer onboarding and context recovery tool for git repositories. It automatically generates living documentation that evolves with every commit, so returning developers can get up to speed instantly and new developers can understand the codebase without reading every file.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## What it does

- **Master Context** (`MASTER_CONTEXT.md`) — A full architectural overview of the codebase, regenerated on every PR merge. Perfect for new developers.
- **Personalized Catchup** (`checkpoints/Checkpoint_<email>.md`) — A "While You Were Gone" briefing per developer, updated on every push. Shows exactly what changed since their last commit.
- **Commit Checkpoints** — Per-commit summaries stored in `checkpoints/`, used as the source material for catchups.
- **PR Summaries** — A consolidated summary for each pull request.

All generation runs via **GitHub Actions** — no local hooks required.

## Installation

```bash
pip install checkpoint-agent
```

## Quick Start

```bash
# Navigate to your git repository
cd /path/to/your/repo

# Install the GitHub Actions workflow + create default config
checkpoint --init
```

Then add your LLM API key as a GitHub Secret (e.g. `MISTRAL_API_KEY`) and push — checkpoints will be generated automatically.

## Commands

```bash
# Setup
checkpoint --init                        # Install GitHub Actions workflow + create config
checkpoint --config                      # Show current configuration

# Generation (also runs automatically via GitHub Actions)
checkpoint --onboard                     # Generate MASTER_CONTEXT.md
checkpoint --catchup                     # Generate your personal catchup
checkpoint --catchup user@email.com      # Generate catchup for a specific user
checkpoint --catchup-all                 # Generate catchups for all active developers

# Commit analysis
checkpoint --commit <hash>               # Analyze a specific commit
checkpoint --commit <hash> --dry-run     # Preview without saving

# Info
checkpoint --stats                       # Show checkpoint statistics
```

## GitHub Actions (recommended)

Run `checkpoint --init` to install the workflow and create the default config, then add your LLM API key as a GitHub secret (e.g. `MISTRAL_API_KEY`).

The workflow runs three jobs automatically:

| Trigger | Job | Output |
|---|---|---|
| Push to any branch | Generate commit checkpoints + catchups for all developers | `checkpoints/Checkpoint-*.md`, `checkpoints/Checkpoint_*.md` |
| PR opened/updated | Generate per-commit checkpoints + PR summary | `checkpoints/PR-*.md` |
| PR merged to main | Regenerate master context | `MASTER_CONTEXT.md` |

## Configuration

`.checkpoint.yaml`:

```yaml
llm:
  provider: mistral          # openai, anthropic, mistral, ollama, google, azure
  model: mistral-medium-2508
  temperature: 0.7
  max_tokens: 2000

repository:
  output_dir: ./checkpoints
  master_context_file: MASTER_CONTEXT.md

features:
  git_hook: false            # Local hook (GitHub Actions is preferred)
  diagrams: true             # Generate Mermaid diagrams in master context
  auto_catchup: false

languages:
  - Python
```

API keys go in `.env`:

```env
MISTRAL_API_KEY=...
# OPENAI_API_KEY=...
# ANTHROPIC_API_KEY=...
```

## Supported LLM Providers

Any provider supported by [LiteLLM](https://github.com/BerriAI/litellm): OpenAI, Anthropic, Mistral, Google Gemini, Azure, Ollama (local), and more. Set `provider` and `model` in `.checkpoint.yaml`.

## Project Structure

```
checkpoint_agent/
├── __main__.py          # CLI entry point
├── agents.py            # LLM prompts (CheckpointGenerator, CatchupGenerator, etc.)
├── graph.py             # Commit analysis pipeline
├── llm.py               # LiteLLM configuration
├── config.py            # Pydantic config models
├── storage.py           # Checkpoint file I/O
├── git_utils.py         # GitPython wrappers
├── mermaid_utils.py     # AST-based diagram generation (Python)
├── llm_diagrams.py      # LLM-based diagram generation (other languages)
├── setup_wizard.py      # Config display utilities
├── git_hook_installer.py
└── templates/
    └── checkpoint.yml   # Bundled GitHub Actions workflow
```

## Development

```bash
git clone https://github.com/BurntDosa/Checkpoint
cd Checkpoint
pip install -e ".[dev]"
pytest tests/
```

## License

MIT
