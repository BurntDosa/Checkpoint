# While You Were Gone (2026-02-11 → Present)

## Changes Summary
- **CI/CD-Centric Checkpoints**:
  - Checkpoints now generated **on push via GitHub Actions** (not locally).
  - Replaces `post-commit` hooks with `pre-push` to reduce local noise.
  - *Impact*: No automatic local checkpoints; push to trigger updates.

- **Storage Layer**:
  - Regex-based filename parsing supports legacy (`YYYY-MM-DD-hash.md`) and new formats (`Author-YYYY-MM-DD-hash.md`).
  - Graceful handling of malformed files.

- **Documentation Cleanup**:
  - Removed 12 legacy markdown files (Jan–Feb 2026), likely transitioning to automated docs (e.g., `MASTER_CONTEXT.md`).

## New Dependencies
- **LiteLLM**: Replaced Mistral-specific code for **multi-provider LLM support**.
- **`.checkpoint.yaml`**: Centralized config for LLM, DB, and git hooks.

## Refactors
- **Git Hooks**: Decoupled local/global environments; hooks now adapt dynamically.
- **Metadata Parsing**: Backward/forward-compatible regex for checkpoint filenames.

## Current Focus
- **Testing**: Validate LiteLLM integrations and git hook reliability.
- **Documentation**: Update workflow diagrams for CI/CD-centric setup.
- **Expansion**: Add language-specific features (e.g., beyond Python).