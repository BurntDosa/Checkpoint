# While You Were Gone — Since 2026-03-05
The past week focused on **CI efficiency** and **developer tooling hygiene**. The GitHub Actions workflow now skips merged commits, reducing redundant runs, while the Code Checkpoint system gained better author filtering and stable filenames. No breaking changes—just smoother workflows.

---

## Critical Changes (Must-Read)
### **GitHub Actions: Merged Commits Now Excluded**
**File**: `.github/workflows/checkpoint.yml`
- **Change**: The workflow now **ignores commits already merged to `main`/`master`** when processing new branches.
  - **Before**: Processed *all* commits in the branch (including duplicates).
  - **After**: Uses `git rev-list ${{ github.sha }} --not origin/main origin/master` to filter.
- **Why It Matters**:
  - Eliminates redundant CI runs for merged commits.
  - Prevents race conditions from reprocessing the same commit.
- **Action Required**: None. This is a backward-compatible improvement.

---

## New Features & Additions
*None in this update.*

---

## Refactors & Structural Changes
### **Code Checkpoint: Cleaner Author Handling**
**Files**: `src/git_utils.py`, `src/storage.py`, `src/agents.py`
1. **Bot Email Exclusion**:
   - Added `BOT_EMAILS` set (e.g., `github-actions[bot]@users.noreply.github.com`) to skip CI agents in catchup generation.
   - **Impact**: Fewer noisy catchups for non-human authors.

2. **Email-Based Filenames**:
   - Filenames now use **sanitized emails** (e.g., `Checkpoint_user@example.com.md`) instead of usernames.
   - **Why**: Emails are stable; usernames may change.

3. **Markdown Template Clarity**:
   - Updated `CatchupSummarizer` to require dynamic dates in headings (e.g., `# While You Were Gone — Since {user_last_active_date}`).

**Action Required**: Only relevant if you maintain the Code Checkpoint system.

---

## New Dependencies & Config Changes
*None in this update.*

---
## Current Focus Areas
*No active projects mentioned in the checkpoints.*