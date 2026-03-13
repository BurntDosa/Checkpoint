## Commit `4376da2` — 2026-03-13

## Context
The catchup feature was incorrectly including the requesting user’s own checkpoints in generated summaries. This meant users received notifications about their own work, which is redundant. The change modifies `get_checkpoints_since()` to accept an optional `exclude_author` parameter, ensuring catchups only contain other team members’ updates.

## Changes
In `checkpoint_agent/core.py`:
- `process_catchup()` now passes `last_commit.get('author')` as `exclude_author` to `get_checkpoints_since()`.
- `get_checkpoints_since()` signature updated to accept `exclude_author: str = None`.
- Added logic to filter out the author’s checkpoint file (e.g., `Checkpoint-{author}.md`) if `exclude_author` is provided.
- Docstring updated to clarify exclusion behavior.

In `pyproject.toml`:
- Version bumped from `1.2.0` to `1.2.1`.

## Impact
Confirmed:
- Catchup summaries no longer include the user’s own checkpoints.
- Version incremented for release tracking.

Likely:
- Reduced noise in catchup outputs, improving relevance.
- No breaking changes for existing callers (optional parameter).

## Priority Rating
**MEDIUM**: Fixes a user-facing annoyance but doesn’t resolve a critical bug or security issue.
