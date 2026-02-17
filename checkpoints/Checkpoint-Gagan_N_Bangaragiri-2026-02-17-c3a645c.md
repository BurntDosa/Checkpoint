# Git Hook Migration: Post-Commit → Pre-Push Checkpoint Generation

## Context
The system previously used a **post-commit** Git hook to generate checkpoints after every local commit. While this ensured comprehensive coverage, it introduced overhead for developers with frequent local commits (e.g., during debugging or WIP changes). The new design shifts checkpoint generation to the **pre-push** hook, triggering only when commits are pushed to a remote repository.

## Changes
### 1. Hook Type Migration
- **From**: `post-commit` (triggered on every `git commit`).
- **To**: `pre-push` (triggered only on `git push`).
- **Rationale**: Reduce noise and overhead during local development while ensuring checkpoints exist for all shared changes.

### 2. Commit Processing Logic
The pre-push hook now:
- Reads Git’s stdin to extract local/remote refs and SHAs.
- Determines the commit range (`$remote_sha..$local_sha`) for the push.
- Skips processing for:
  - Branch deletions (`local_sha = 000...000`).
  - New branches with no prior commits (`remote_sha = 000...000`).
- Generates checkpoints **synchronously** for each commit in the range.

### 3. Auto-Catchup
- Moved from post-commit to pre-push.
- Still triggered via `--catchup-all`, but now runs during pushes.

### 4. Backward Compatibility
- **Uninstall**: Removes both pre-push and legacy post-commit hooks.
- **Status Checks**: Detects old post-commit hooks (`old_post_commit` flag).

### 5. User Feedback
- Added progress messages (e.g., `Processing commit: $commit`).
- Success/failure notifications during push.

## Impact
### Performance
- ✅ **Reduced Local Overhead**: No checkpoint generation during local commits.
- ⚠️ **Slightly Longer Pushes**: Synchronous checkpoint generation may add minimal latency to `git push`.

### Data Consistency
- ✅ **Atomic Pushes**: Checkpoints are generated for all commits in a push *before* the push completes.
- ✅ **Branch Awareness**: Explicit handling of branch creation/deletion.

### Collaboration
- ✅ **Focus on Shared Changes**: Checkpoints are now tied to pushed commits, aligning with team workflows.
- ⚠️ **Less Frequent Auto-Catchup**: Runs only during pushes (not commits), but ensures summaries are up-to-date for shared branches.

### Migration
- **Action Required**: Users must uninstall the old post-commit hook and install the new pre-push hook.
- **Cleanup**: The system automatically detects and removes legacy hooks during uninstallation.

## Example Workflow
```bash
# Old behavior (post-commit)
git commit -m "WIP"  # Triggers checkpoint (even for temporary commits)
git push             # No additional checkpoints

# New behavior (pre-push)
git commit -m "WIP"  # No checkpoint
git push             # Triggers checkpoints for all commits in the push
```

## How to Upgrade
1. Uninstall the old hook:
   ```bash
   python -m git_hook_installer uninstall