# Git Hook Installer: Development Mode Support

## Context
The `git_hook_installer.py` script is responsible for generating and installing git hooks that automatically trigger the `checkpoint` tool after each commit. Previously, the hook assumed the `checkpoint` command was globally installed, which created friction for developers working on the tool itself.

## Changes
### 1. Development Mode Detection
- Added `repo_root: Optional[Path]` parameter to `get_hook_template` to detect if the repository is in "development mode" (i.e., contains `main.py` and a virtual environment at `.venv/bin/python`).
- If in dev mode, the hook dynamically generates a command to execute `main.py` directly using the virtual environment's Python interpreter:
  ```bash
  ".venv/bin/python main.py" --commit "$COMMIT_HASH"
  ```
- Otherwise, it falls back to the default `checkpoint` command.

### 2. Dynamic Hook Template Generation
- The hook template now uses f-strings to inject the dynamic `checkpoint_cmd` into both the `--commit` and `--catchup-all` calls.
- Example generated hook (dev mode):
  ```sh
  #!/bin/sh
  COMMIT_HASH=$(git rev-parse HEAD)
  ".venv/bin/python" "main.py" --commit "$COMMIT_HASH" >> .checkpoint.log 2>&1 &
  ```

### 3. Repository Root Handling
- Updated `install_hook` to extract the `repo_root` from the `.git` directory's parent and pass it to `get_hook_template`.

## Impact
### Architectural
- **Decoupling**: The hook no longer depends on a global `checkpoint` installation, improving portability.
- **Environment Awareness**: Introduces dynamic behavior based on the repository's structure, which could be extended to other scripts.
- **Backward Compatibility**: Non-dev environments are unaffected; the hook defaults to the original behavior.

### Development Workflow
- **Seamless Local Testing**: Developers can now test `checkpoint` changes directly from the source code without reinstalling the tool globally.
- **Reduced Friction**: Eliminates the need to manually switch between global and local installations during development.

### Risks and Mitigations
- **Risk**: Incorrect dev mode detection could lead to failed hook execution.
  - **Mitigation**: The logic checks for both `main.py` and `.venv/bin/python` before switching to dev mode.
- **Risk**: Virtual environment paths may vary across platforms.
  - **Mitigation**: The path construction uses `Path` objects for cross-platform compatibility.