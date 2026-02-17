# While You Were Gone (2026-02-17 → Present)

## Changes Summary
- **Architectural Shift**: Migrated from local git hooks to **CI/CD-driven checkpoint generation** (GitHub Actions).
  - Checkpoints now created *only on push* (`pre-push` hook), reducing local overhead.
  - Legacy `post-commit` hooks and bulk `--onboard` commands removed.
- **Storage Layer**:
  - Regex-based filename parsing supports both legacy (`YYYY-MM-DD-hash.md`) and new formats (`Checkpoint-Author-YYYY-MM-DD-hash.md`).
  - ChromaDB cleanup removed binary files; metadata extraction is now fault-tolerant.
- **Documentation**: Purged 12 historical checkpoint files (Jan–Feb 2026), likely replaced by **automated `MASTER_CONTEXT.md`**.

## New Dependencies
| Dependency       | Purpose                                                                 |
|------------------|-------------------------------------------------------------------------|
| **LiteLLM**      | Replaces Mistral-specific code; enables **multi-provider LLM support** (OpenAI, Anthropic, etc.). |
| **Pydantic**     | Powers the new **interactive setup wizard** for language/config validation. |
| **GitHub Actions** | Core workflow (`checkpoint.yml`) now handles checkpoint generation.   |

## Refactors
1. **CLI & Workflow**:
   - `--onboard` → `--commit <hash>` for granular checkpoint generation.
   - `--catchup-all` retained for summaries but decoupled from commit processing.
2. **Configuration**:
   - `.checkpoint.yaml` centralizes LLM, DB, and git hook settings.
   - Git hooks **disabled by default** (`install_git_hook = False`).
3. **Error Handling**:
   - Silences `git rev-list` errors (e.g., no new commits).
   - Skips malformed checkpoint files gracefully.

## Current Focus
- **Testing**: Validate LiteLLM integrations and git hook reliability across environments.
- **Documentation**: Update architecture diagrams for CI/CD workflows.
- **Scalability**:
  - Expand language support (beyond Python prototype).
  - Optimize **multi-LLM provider** performance.
- **Trade-offs to Monitor**:
  - Latency: Checkpoints generated only on push (not locally).
  - CI/CD dependency: Requires GitHub Actions uptime.

> **Action Items for You**:
> - Run `python main.py --commit <hash>` to test granular checkpoint generation locally.
> - Review `.checkpoint.yaml` for LLM/DB configurations.
> - Check `MASTER_CONTEXT.md` for consolidated documentation.