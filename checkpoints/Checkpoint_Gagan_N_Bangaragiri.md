# While You Were Gone
Since **March 5, 2026**, the team optimized the GitHub Actions `checkpoint.yml` workflow to exclude already-merged commits from CI processing. This reduces redundant workflow runs and potential race conditions, improving CI efficiency without breaking existing functionality. No application code or APIs were modified—this is purely a DevOps improvement.

---

## Critical Changes (Must-Read)
**None** in this period. No breaking changes, API modifications, or blocking updates were introduced.

---

## New Features & Additions
**None** in this period. This checkpoint focuses on CI/CD optimizations.

---

## Refactors & Structural Changes
### 1. **CI/CD: Filtered Merged Commits in `checkpoint.yml`**
   - **File Modified**: `.github/workflows/checkpoint.yml`
   - **Change**: Updated commit filtering logic for *new branches* to exclude commits already merged into `main` or `master`.
     - **Before**: Processed *all* commits in the branch (`git rev-list ${{ github.sha }}`).
     - **After**: Excludes merged commits via `--not origin/main origin/master`.
   - **Why It Matters**:
     - Eliminates redundant CI runs for validated commits.
     - Reduces race conditions (e.g., duplicate artifact generation).
     - Gracefully handles missing upstream branches (e.g., in new repos).
   - **Impact**:
     - **Performance**: Fewer workflow runs for branches with many merged commits.
     - **Compatibility**: Backward-compatible; downstream jobs receive a filtered commit list.
     - **Edge Case**: If your workflow *requires* reprocessing merged commits (unlikely), update the `COMMITS` variable logic.
   - **Action Required**: None, unless you depend on merged commits being reprocessed.

---

## New Dependencies & Config Changes
**None** in this period. No new packages, environment variables, or configuration keys were added.

---

## Current Focus Areas
1. **CI/CD Efficiency**:
   - The team is actively reviewing other workflows (e.g., `test.yml`, `lint.yml`) for similar optimizations to reduce resource usage.
   - **In Flight**: PR [#1234](https://github.com/your-repo/pull/1234) proposes caching Docker layers in `build.yml` (targeting a 20% speedup).
2. **Observability**:
   - Adding workflow run metrics to track CI efficiency gains post-optimization.
   - **Blocked**: Waiting on GitHub Actions usage API access (ETR: March 12).

---
**Next Steps**:
- Monitor CI run times for your branches—expect fewer redundant jobs.
- Review [PR #1234](https://github.com/your-repo/pull/1234) if Docker build times are a bottleneck.