# While You Were Gone — Since 2026-02-11

The **Code Checkpoint system** has undergone a **major architectural shift** since your last activity, transitioning from a local git hook-driven tool to a **CI/CD-centric, language-agnostic platform**. The most critical changes include **disabling local hooks by default** (checkpoints now generate only on push via GitHub Actions), **email-based filenames** for stability, and **multi-LLM support** via LiteLLM. These updates improve scalability but require adjustments to your workflow—particularly if you relied on local checkpoint generation or username-based catchups.

---

## Critical Changes (Must-Read)

### 1. Git Hooks and CI/CD Takeover
- **What Changed**:
  - **Local git hooks (`post-commit` → `pre-push`)** are now **disabled by default** (`install_git_hook = False` in `setup.py`).
  - Checkpoints are **only generated in GitHub Actions** on push (via `checkpoint.yml`), using `git rev-list` to process commits dynamically.
  - The `--onboard` command is **deprecated**; use `--commit <hash>` for granular checkpoint generation.

- **Why It Matters**:
  - **Breaking Change**: If you relied on local checkpoints, you’ll need to **push changes** to trigger updates.
  - **Action Required**: Update your `setup.py` to reflect:
    ```python
    install_git_hook = False  # Explicitly disabled
    auto_catchup = False      # No local auto-generation
    ```

### 2. Storage Layer: Email-Based Filenames and Bot Exclusion
- **What Changed**:
  - Catchup filenames now use **sanitized emails** (e.g., `Checkpoint_user@example.com.md`) instead of usernames, preventing breaks if usernames change.
  - **CI bots** (e.g., `github-actions[bot]`) are **automatically excluded** from catchup summaries via `BOT_EMAILS` in `git_utils.py`.

- **Why It Matters**:
  - **Breaking Change**: Scripts referencing username-based filenames (e.g., `Checkpoint_John_Doe.md`) will fail. Update to use emails.
  - **Action Required**: Add your CI bot emails to `BOT_EMAILS` to avoid noisy catchups:
    ```python
    BOT_EMAILS = {
        "github-actions[bot]@users.noreply.github.com",
        "your-ci-bot@example.com",  # Add yours here
    }
    ```

### 3. CI/CD Commit Filtering
- **What Changed**:
  The `checkpoint.yml` workflow now **skips commits already merged to `main`/`master`** for new branches, reducing redundant processing.
  - **Before**: All commits in a branch were processed.
  - **After**: Only commits **not** in `origin/main` or `origin/master` are included.

- **Impact**:
  - Fewer duplicate workflow runs, but ensure your branch is up-to-date with `main` to avoid missing context.

---

## New Features & Additions

### 1. Multi-LLM Support via LiteLLM
- **What’s New**:
  - Replaced Mistral-specific code with **LiteLLM**, enabling integration with **any LLM provider** (OpenAI, Anthropic, etc.).
  - Configure providers in `.checkpoint.yaml`:
    ```yaml
    llm:
      provider: "openai"  # or "anthropic", "mistral", etc.
      api_key: "${OPENAI_API_KEY}"
    ```

- **Why It Matters**:
  - **No vendor lock-in**: Switch providers without code changes.
  - **Fallback support**: Automatically retries failed requests across providers.

### 2. Interactive Setup Wizard
- **What’s New**:
  - A **Pydantic-based config wizard** guides users through:
    - Language detection (e.g., Python, JavaScript).
    - LLM provider selection.
    - Git hook preferences.
  - Run it with:
    ```bash
    python -m checkpoint.setup
    ```

- **Impact**:
  - Simplifies onboarding for new developers and reduces misconfiguration.

### 3. Granular Checkpoint Generation
- **What’s New**:
  - Generate checkpoints for **specific commits** using:
    ```bash
    python main.py --commit <hash>
    ```
  - Replaces the bulk `--onboard` command for targeted updates.

- **Use Case**:
  - Debugging changes in a specific commit without processing the entire branch.

---

## Refactors & Structural Changes

### 1. Regex-Based Metadata Parsing
- **What Changed**:
  - The storage layer now uses **regex** to parse filenames like:
    - Legacy: `YYYY-MM-DD-hash.md`
    - New: `Checkpoint-Author-YYYY-MM-DD-hash.md`
  - **Graceful degradation**: Skips malformed files instead of crashing.

- **Impact**:
  - **Forward/backward compatible**: Supports future filename formats without breaking existing checkpoints.

### 2. Decoupled Local vs. CI Workflows
- **What Changed**:
  - Local development no longer requires git hooks or auto-catchup.
  - **Core features** (Vector DB, diagrams) remain functional without local hooks.

- **Developer Workflow**:
  - Test changes directly from source code without global installations.
  - Push to trigger CI/CD-generated checkpoints.

### 3. Centralized Configuration (`.checkpoint.yaml`)
- **What Changed**:
  - All settings (LLM, DB, git hooks) are now managed in `.checkpoint.yaml`:
    ```yaml
    git:
      install_hook: false
    llm:
      provider: "openai"
    storage:
      path: "./checkpoints"
    ```

- **Impact**:
  - **Single source of truth**: No more scattered environment variables