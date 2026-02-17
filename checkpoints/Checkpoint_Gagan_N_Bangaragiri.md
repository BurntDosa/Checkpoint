# While You Were Gone

## Changes Summary
- **Git Hooks**: Migrated from `post-commit` to `pre-push` (reduces local noise).
- **CI/CD Integration**: Checkpoints now generated via GitHub Actions on push (not locally).
- **Historical Cleanup**: 12 legacy checkpoint files deleted (Jan–Feb 2026), signaling a shift to automated docs (e.g., `MASTER_CONTEXT.md`).
- **CLI**: `--commit <hash>` replaces `--onboard` for per-commit updates.

## New Dependencies
- **LiteLLM**: Multi-provider LLM support (replaces Mistral-specific code).
- **GitHub Actions**: Required for checkpoint generation (previously local hooks).

## Refactors
- **Storage Layer**: Regex-based metadata parsing for filename compatibility.
- **Setup**: Git hooks/auto-catchup **disabled by default** (simplifies local setup).
- **Config**: Centralized `.checkpoint.yaml` for LLM, DB, and git settings.

## Current Focus
- **Testing**: LLM integrations and git hook reliability.
- **Documentation**: Updating diagrams/setup guides for new workflows.
- **Expansion**: Adding language-specific features (beyond Python).