# While You Were Gone — Since 2026-02-11
The past week saw a targeted CI/CD improvement to eliminate version skew between workflows and the local codebase. No application logic or APIs were modified, but workflows now install the project in editable mode (`pip install .`) instead of pulling from PyPI. This ensures PR testing and context updates use the exact code under review.

## Critical Changes (Must-Read)
**None.** This update is purely a workflow improvement with no breaking changes or immediate action required.

## New Features & Additions
**None.** No new capabilities were introduced.

## Refactors & Structural Changes
### CI/CD Workflow Fixes
- **Problem**: Workflows previously installed the published `checkpoint-agent` package from PyPI, risking mismatches between tested code and the workflow environment (e.g., during PR validation).
- **Solution**: Modified three jobs in `.github/workflows/checkpoint.yml` and its template to use `pip install .` (editable mode):
  1. **Run Checkpoint Agent & Update Contexts** (line 30)
  2. **Generate Per-Commit Checkpoints & PR Summary** (line 96)
  3. **Regenerate Master Context** (line 160)
- **Impact**:
  - Workflows now reflect the repo’s current state, not a released version.
  - No changes to job logic or outputs; only the installation method differs.

## New Dependencies & Config Changes
**None.** The dependency graph remains unchanged.

## Current Focus Areas
- **CI/CD Reliability**: The team is prioritizing workflow consistency to reduce false negatives in PR testing.
- **Next Steps**: Monitor for edge cases where editable-mode installs might behave differently (e.g., path resolution in submodules).

---
**Action Items for You**:
- If you encounter unexpected CI failures, verify whether the issue persists with `pip install .` locally.
- No code changes are needed, but be aware that workflows now test *exactly* what’s in your PR branch.