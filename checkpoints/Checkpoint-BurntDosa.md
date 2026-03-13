## Commit `a2cbd41` — 2026-03-13

## Context
Catchups were accidentally including checkpoint entries from before a user joined the repo, creating noise in the LLM-generated summaries. The commit addresses this by:
1. Adding date filtering in `get_checkpoints_since()` to only return entries on/after the user’s last active date (parsed from `## Commit` headers).
2. Cleaning up the date formatting in `process_catchup()` to show user-friendly dates (e.g., "March 13, 2026") instead of raw datetime strings.

## Changes
In `checkpoint_agent/checkpoints.py`:
- Added `_filter_entries_after()`: Parses checkpoint files into individual commit entries (split on `## Commit` headers) and filters out entries older than `since_date`. Uses regex to extract dates from headers like `## Commit \`hash\` — YYYY-MM-DD`.
- Modified `get_checkpoints_since()`:
  - Replaced `read_file()` with `read_and_filter()` to apply `_filter_entries_after()` to each file.
  - Updated docstring to clarify `since_date` is now used for content filtering, not just LLM prompting.
- Updated `process_catchup()` in same file:
  - Added logic to format `last_commit['date']` as "Month Day, Year" before passing to `CatchupGenerator`.

In `pyproject.toml`:
- Bumped version from `1.2.1` to `1.2.2`.

## Impact
Confirmed:
- `get_checkpoints_since()` now returns only entries dated on/after `since_date`.
- Catchup prompts show formatted dates (e.g., "March 13, 2026") instead of raw datetimes.
- Version bumped to `1.2.2`.

Likely:
- Smaller, more relevant catchup contexts for users, reducing LLM noise.
- No breaking changes to the API, but consumers relying on raw date strings in prompts may need updates.

## Priority Rating
HIGH: Fixes a core functionality issue (irrelevant historical data in catchups) and improves user-facing date readability, justifying a patch release.
