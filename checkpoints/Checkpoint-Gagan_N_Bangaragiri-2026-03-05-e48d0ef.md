# Checkpoint Workflow Optimization: Exclude Merged Commits

## Context
The `checkpoint.yml` GitHub Actions workflow processes commits pushed to a branch, typically for tasks like linting, testing, or generating artifacts. Previously, when a new branch was pushed, the workflow would process *all* commits in the branch, including those already merged to `main` or `master`. This could lead to:
- Redundant workflow runs for commits already validated.
- Potential race conditions if the same commit was processed multiple times.
- Unnecessary CI load, especially in active repositories with long-lived branches.

## Changes
### `.github/workflows/checkpoint.yml`
- **Commit Filtering for New Branches**:
  Updated the logic for new branches (where `github.event.before` is `0000...0`) to exclude commits that already exist on `origin/main` or `origin/master`.
  - **Before**: `COMMITS=$(git rev-list ${{ github.sha }})` (all commits in the branch).
  - **After**: `COMMITS=$(git rev-list ${{ github.sha }} --not origin/main origin/master 2>/dev/null || echo "")`
    - `--not origin/main origin/master`: Explicitly excludes merged commits.
    - Error handling (`2>/dev/null || echo ""`) ensures the workflow doesn’t fail if upstream branches are missing.

- **No Changes for Existing Branches**:
  The logic for existing branches (comparing `github.event.before` to `github.sha`) remains unchanged.

## Impact
### Architectural Impact
- **Scope**: Limited to the GitHub Actions workflow layer. No application code or data models are affected.
- **Data Flow**: The `COMMITS` variable now passes a filtered list to downstream jobs, which may reduce the number of commits processed. This is intentional and improves efficiency.
- **Ripple Effects**:
  - Downstream CI jobs (e.g., tests, linters) will run less frequently for branches with many merged commits, reducing resource usage.
  - No breaking changes: Workflows depending on *all* commits (including merged ones) are edge cases and likely unintended.
- **Breaking Changes**: None. The update is backward-compatible and aligns with the expected behavior of processing only *new* commits.

### Performance Benefits
- **Reduced Redundancy**: Avoids reprocessing commits already validated on `main`/`master`.
- **Robustness**: Gracefully handles missing upstream branches (e.g., in new repos) without failing.

## Priority Rating
**MEDIUM**: This change improves CI efficiency and reliability without risking breaking changes. While not critical, it reduces operational overhead and potential confusion from duplicate workflow runs. Teams with high CI costs or active branching will benefit the most.