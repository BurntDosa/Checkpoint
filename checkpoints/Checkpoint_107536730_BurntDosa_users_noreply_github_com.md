# While You Were Gone — Since 2026-03-06 12:17:08+05:30
The project has undergone **major architectural shifts**—most critically, a **migration from DSPy to LiteLLM** for LLM orchestration, a **switch from local git hooks to GitHub Actions**, and a **repository ownership transfer** to `BurntDosa/Checkpoint`. These changes break backward compatibility in key areas (CLI workflows, LLM abstractions, and config handling), but they resolve long-standing issues like hook failures, ChromaDB overhead, and provider limitations. **Your immediate focus should be on updating LLM-related code, CI/CD pipelines, and GitHub Actions workflows.**

---

## Critical Changes (Must-Read)
### 1. **DSPy → LiteLLM Migration (Breaking)**
   - **Files**: `checkpoint_agent/agents.py`, `checkpoint_agent/llm.py`
   - **Impact**:
     - **All DSPy abstractions removed**: `dspy.Signature`, `dspy.Module`, and `dspy.Prediction` are gone. Agents now use **raw LiteLLM calls** with `SimpleNamespace` returns.
     - **Configuration**: `configure_llm()` no longer returns an object; it sets a module-level `_llm_config` dict.
     - **Error handling**: Replace `dspy.LMException` with `litellm.BadRequestError`.
     - **Testing**: Mock `litellm.completion` instead of `dspy.predictor.forward`.
   - **Action Required**:
     - Update **all imports** (remove `dspy`, add `types.SimpleNamespace`).
     - Rewrite tests to mock `litellm.completion`.
     - Verify prompts (now raw strings in `__call__` methods).

### 2. **Git Hooks → GitHub Actions (Breaking)**
   - **Files**: `checkpoint_agent/setup_wizard.py`, `.github/workflows/checkpoint.yml`
   - **Impact**:
     - **Local hooks disabled by default**: `.checkpoint.yaml` now sets `git_hook: false`.
     - **New CLI command**: `checkpoint --install-ci` scaffolds a GitHub Actions workflow.
     - **API keys moved to GitHub Secrets** (e.g., `MISTRAL_API_KEY`). **Local `.env` files are obsolete**.
     - **GitHub Actions fixes**:
       - Multi-committer support: Skips **all** authors in a push (not just the pusher).
       - Recursive file staging: `git add checkpoints/` (replaces glob patterns).
   - **Action Required**:
     - Run `checkpoint --install-ci` to migrate.
     - Add LLM API keys as **GitHub Secrets**.
     - Update CI/CD to use `checkpoint --catchup-all --catchup-skip "email1,email2"`.

### 3. **Repository Migration (Metadata Only)**
   - **File**: `pyproject.toml`
   - **Impact**:
     - **Author/email updated** to `Gagan N Bangaragiri <gagan.bangaragiri@gmail.com>`.
     - **All GitHub links** now point to [`BurntDosa/Checkpoint`](https://github.com/BurntDosa/Checkpoint).
     - **No code changes**, but CI/CD pipelines referencing the old repo (`checkpoint-agent/checkpoint`) will fail.
   - **Action Required**:
     - Update `actions/checkout` steps in GitHub Actions:
       ```yaml
       - uses: actions/checkout@v3
         with:
           repository: BurntDosa/Checkpoint  # NEW
       ```

### 4. **ChromaDB and Semantic Search Removed**
   - **Files**: `README.md`, `checkpoint_agent/agents.py`
   - **Impact**:
     - **Vector search deleted**: `vector_db_path` config key and ChromaDB dependencies removed.
     - **Simplified architecture**: Agents now use **direct LLM analysis** (no AST parsing or embeddings).
   - **Action Required**:
     - Remove `vector_db: true` from `.checkpoint.yaml` (if present).
     - Replace any `CheckpointGenerator` calls expecting ChromaDB outputs.

---

## New Features & Additions
### 1. **GitHub Actions Integration**
   - **Auto-triggered checkpoints**: Runs on `push`, `pull_request`, and `merge` to `main`.
   - **Multi-email skip**: `--catchup-skip` now accepts comma-separated emails (e.g., `--catchup-skip "dev1@company.com,dev2@company.com"`).
   - **Workflows**:
     - `checkpoint --install-ci` generates a preconfigured `.github/workflows/checkpoint.yml`.
     - Outputs are auto-staged with `git add checkpoints/`.

### 2. **LiteLLM Provider Flexibility**
   - **Support for 50+ providers**: Use strings like `"groq/llama3-70b"` or `"mistral/mistral-small"` in config.
   - **Simplified routing**: `drop_params=True` ignores unsupported args (e.g., `top_p` for Mistral).
   - **Debugging**: Enable with `litellm.set_verbose=True`.

### 3. **Prompt Guardrails**
   - **Anti-hallucination disclaimers**: Catchup templates now explicitly forbid invented metadata (e.g., PR numbers, team names).
   - **Example**:
     ```markdown
     IMPORTANT: Only include information explicitly stated in the checkpoints.
     Do not invent team member names, owners, PR numbers, or work items.
     ```

### 4. **New CLI Commands**
   | Command               | Purpose                                                                 |
   |-----------------------|-------------------------------------------------------------------------|
   | `--install-ci`        | Generates a GitHub Actions workflow file.                               |
   | `--stats`             | Shows checkpoint generation metrics (e.g., files processed, LLM tokens). |
   | `--catchup-skip`      | Skips multiple emails (comma-separated).                                |

---

## Refactors & Structural Changes
### 1. **Agents Simplified**
   - **File**: `checkpoint_agent/agents.py`
   - **Before**: 520 lines (DSPy abstractions).
   - **After**: 160 lines (raw LiteLLM calls).
   - **Key changes**:
     - `CheckpointGenerator`, `CatchupGenerator`: Now flat classes with `__call__` methods.
     - Prompts are **inline strings** (no `dspy.InputField`).
     - Returns `SimpleNamespace` (replaces `dspy.Prediction`).

### 2. **Configuration Overhaul**
   - **File**: `.checkpoint.yaml`
   - **Removed keys**:
     ```yaml
     vector_db: true
     vector_db_path: ./chroma
     ignore_patterns: ["*.lock"]
     file_patterns: ["**.py"]
     ```
   - **New defaults**:
     ```yaml
     features:
       git_hook: false  # Disabled by default