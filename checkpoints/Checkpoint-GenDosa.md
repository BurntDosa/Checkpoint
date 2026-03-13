## Commit `c0dbe15` — 2026-03-13

## Context
The issue arose from timezone mismatches between git commit timestamps (which include the committer's local timezone, e.g., +05:30 IST) and checkpoint entry dates (written in UTC by the CI runner). When a commit occurred just after midnight in IST (e.g., 2026-03-14 00:19), the cutoff date was March 14, but the corresponding checkpoint entry—written at the same instant in UTC—was dated March 13. This caused `_filter_entries_after()` to filter out *all* entries as "No checkpoints found since last activity," breaking context recovery.

## Changes
**File: `checkpoint_agent/filter.py`**
- Modified `_filter_entries_after()` to normalize `since_date` to UTC before extracting the date for comparison.
- Added logic to subtract `since_date.utcoffset()` when the datetime is timezone-aware (confirmed via `hasattr(since_date, 'utcoffset')` and `utcoffset() is not None`).
- Fallback to original behavior (`since_date.date()`) for naive datetimes or non-datetime objects.

**File: `pyproject.toml`**
- Bumped version from `1.2.2` to `1.2.3`.

## Impact
**Confirmed:**
- `_filter_entries_after()` now correctly compares dates across timezones, resolving the "No checkpoints found" false negative.
- Version bump ensures users pull the fix.

**Likely:**
- Restores expected behavior for users in timezones ahead of UTC (e.g., IST, CET) during daylight saving transitions or near midnight commits.
- No impact on UTC or timezone-naive inputs (fallback path unchanged).

## Priority Rating
**HIGH**: Fixes a critical data loss scenario where users lose all checkpoint context after commits near timezone boundaries.

---

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
