## Commit `3f0ac52` — 2026-03-14

## Context
This change cleans up the repository by removing tracked files that shouldn't be committed (checkpoints, tests, `.DS_Store`) and updates documentation. The commit message indicates this is a housekeeping task to prevent the checkpoint system from running on its own repo, which would create recursive/self-referential artifacts.

## Changes

**.gitignore**
- Added `checkpoints/`, `catchups/`, `tests/`, `CLAUDE.md`, and `MASTER_CONTEXT.md` to ignored paths
- Updated comment for clarity: `# Code Checkpoint specific (don't run checkpoint on its own repo)`

**Removed files (untracked in git)**
- Deleted `CLAUDE.md` (47-line documentation file with architecture, commands, and conventions)
- Deleted `tests/` directory (contained at least `test_mermaid_utils.py`)
- Deleted `checkpoints/` directory (all checkpoint files)
- Removed `.DS_Store` (macOS metadata file)

**README.md** (renamed from `README.md` to `Checkpoint.md` in commit but content shows it's the same file)
- Added banner image (`assets/banner.png`)
- Renamed project title from "Code Checkpoint" to "Checkpoint"
- Updated feature descriptions to match new folder structure (`catchups/` instead of `checkpoints/` for catchup files)
- Added `--install-hook` and `--uninstall` commands
- Added `checkpoint --pr` command documentation
- Updated config example with new fields (`ignore_patterns`, `file_patterns`, increased `max_tokens` from 2000 to 8000)
- Clarified catchup file lifecycle: "When a developer commits, their catchup file is automatically deleted (they're caught up)"

**New file**
- Added `assets/banner.png` (binary image)

## Impact
- **Confirmed**: The repo no longer tracks checkpoint artifacts, tests, or `.DS_Store` files
- **Confirmed**: Documentation now reflects the correct folder structure and command set
- **Confirmed**: `.gitignore` prevents future accidental commits of checkpoint/test files
- **Likely**: Local development will be cleaner without generated files in git status
- **Likely**: The increased `max_tokens` value in docs suggests the system now handles larger commits
- **Likely**: The new `ignore_patterns` and `file_patterns` config options provide more control over analyzed files

## Priority Rating
**MEDIUM** — This is a housekeeping change that prevents repository pollution but doesn't affect core functionality for end users.
