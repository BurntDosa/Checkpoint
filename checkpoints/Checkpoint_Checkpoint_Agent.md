# While You Were Gone
Since **February 17, 2026**, the Code Checkpoint system has undergone a **fundamental shift from local to CI/CD-driven workflows**, deprecating git hooks in favor of GitHub Actions. This change **breaks local checkpoint generation** but improves consistency and reduces redundancy. Critical updates include **LiteLLM integration** (replacing Mistral-specific code), **regex-based storage parsing** (for backward/forward-compatible filenames), and **smart commit filtering** in CI to skip already-merged changes. The system is now **language-agnostic** and relies on `.checkpoint.yaml` for centralized config.

---

## Critical Changes (Must-Read)
### 1. **Checkpoints Now Generated Exclusively in CI/CD**
   - **What Changed**:
     - Local git hooks (`post-commit`/`pre-push`) are **disabled by default** (`install_git_hook = False` in `setup.py`).
     - Checkpoints are now generated **only in GitHub Actions** via `.github/workflows/checkpoint.yml`, triggered on `git push`.
     - The `--onboard` bulk command is **deprecated**; use `--commit <hash>` for granular updates or `--catchup-all` for summaries.
   - **Why It Matters**:
     - **Breaking Change**: Local commits **will not** generate checkpoints until pushed. This affects testing and iterative development.
     - CI/CD is now the **single source of truth** for checkpoint data.
   - **Action Required**:
     - Disable local hooks if enabled: `python setup.py --disable-hooks`.
     - Update scripts/relying on `post-commit` hooks to use `pre-push` or CI triggers.
     - Test CI-driven checkpoints by pushing a small change and verifying `.github/workflows/checkpoint.yml` runs.

### 2. **Git Hook Migration: `post-commit` → `pre-push`**
   - **Files Affected**: `.githooks/pre-push`, `setup.py`, `main.py`.
   - **Impact**:
     - Hooks now trigger **only on `git push`**, not `git commit`. This reduces noise but may delay feedback.
     - **Backward Incompatible**: Existing `post-commit` hooks will fail silently.
   - **Workaround**:
     - Manually run `python main.py --commit <hash>` to generate local checkpoints for testing.

### 3. **CI Workflow Now Excludes Merged Commits**
   - **Change**: `.github/workflows/checkpoint.yml` uses `git rev-list ${{ github.sha }} --not origin/main origin/master` to skip commits already in `main`/`master`.
   - **Risk**:
     - If your branch is **not up-to-date with `main`**, some commits may be skipped unexpectedly.
     - Workflows depending on *all* commits (e.g., full-history analysis) will now receive a filtered list.
   - **Fix**:
     - Ensure branches are rebased on `main` before pushing.
     - For full-history processing, temporarily modify the workflow to remove `--not origin/main`.

### 4. **Storage Layer: Regex-Based Filename Parsing**
   - **Breaking Change**: Legacy checkpoint filenames (e.g., `2026-01-13-hash.md`) are **still supported**, but new files must use the format `Checkpoint-Author-YYYY-MM-DD-hash.md`.
   - **Files Affected**: `storage.py`, any scripts reading checkpoint metadata.
   - **Action**:
     - Audit custom scripts for hardcoded filename assumptions.
     - Test with mixed legacy/new filenames to ensure no regessions.

---

## New Features & Additions
### 1. **LiteLLM Integration (Multi-Provider LLM Support)**
   - **What’s New**:
     - Replaced Mistral-specific code with **LiteLLM**, enabling pluggable LLM providers (e.g., OpenAI, Anthropic, local models).
     - Configurable via `.checkpoint.yaml`:
       ```yaml
       llm:
         provider: "openai"  # or "mistral", "anthropic", etc.
         model: "gpt-4-turbo"
         api_key: "${LLM_API_KEY}"  # Loaded from env vars
       ```
   - **Impact**:
     - **No more vendor lock-in**: Switch providers by updating config.
     - **Cost control**: Use cheaper/faster models for non-critical tasks.
   - **Setup**:
     - Install LiteLLM: `pip install litellm`.
     - Set `LLM_API_KEY` in your environment or GitHub Secrets.

### 2. **Interactive Setup Wizard**
   - **New Command**: `python setup.py --wizard` guides users through:
     - Language detection (auto-configures parsers for Python, JS, etc.).
     - LLM provider selection.
     - Git hook preferences.
   - **Use Case**: Onboard new team members or validate config changes.

### 3. **Per-Commit Checkpoint Generation**
   - **New CLI Argument**: `--commit <hash>` generates a checkpoint for a specific commit.
     ```bash
     python main.py --commit a1b2c3d  # Process a single commit
     ```
   - **CI Integration**: GitHub Actions now processes commits individually (see [Critical Changes](#critical-changes-must-read)).

### 4. **Centralized Configuration (`.checkpoint.yaml`)**
   - **New File**: Consolidates settings previously in `setup.py`, `config.json`, and env vars.
     ```yaml
     git:
       auto_hook_install: false  # Default: false (was true)
     storage:
       path: "./checkpoints"
       db: "chromadb"  # or "weaviate", "pinecone"
     ```
   - **Migration**:
     - Run `python setup.py --migrate-config` to auto-generate `.checkpoint.yaml` from legacy files.
     - **Deprecated**: `config.json` and `CHECKPOINT_DB_URL` env var (use `.checkpoint.yaml` instead).

---

## Refactors & Structural Changes
### 1. **Storage Layer Overhaul**
   - **Old**: Fragile string-splitting for filenames (e.g., `split("-")[0]` for dates).
   - **New**: Regex-based parsing supporting:
     - Legacy: `YYYY-MM-DD-hash.md`
     - New: `Checkpoint-Author-YYYY-MM-DD-hash.md`
   - **Performance**: Skips malformed files instead of crashing.
   - **Files Changed**: `storage.py`, `utils/parsers.py`.

### 2. **Git Hook Decoupling**
   - **Before**: Hooks were tightly coupled to global Python installations.
   - **After**:
     - Hooks run from the local repo’s `.venv` (if present).
     - **No global dependencies**: Test changes without `pip install -e`.
   - **Testing**:
     - Verify hooks work in both global and local venv contexts:
       ```bash
       git config core.hooksPath .githooks  # Enable hooks
       git push --dry-run  # Test pre-push hook