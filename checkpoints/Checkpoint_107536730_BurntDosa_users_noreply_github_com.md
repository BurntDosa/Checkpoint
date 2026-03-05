# While You Were Gone
Between **February 11–28, 2026**, the Code Checkpoint system underwent a **fundamental shift from local git hooks to CI/CD-driven workflows**, eliminating redundant local processing and centralizing checkpoint generation in GitHub Actions. This change **breaks local auto-generation** (now opt-in) but improves consistency and reduces noise. Critical updates include **multi-LLM support (LiteLLM)**, a **new `--commit <hash>` CLI argument**, and **regex-based metadata parsing** for backward compatibility. The team also **purged 12 legacy checkpoints** (Jan–Feb 2026), hinting at a move toward automated documentation (e.g., `MASTER_CONTEXT.md`).

---

## Critical Changes (Must-Read)
### 🚨 Breaking Changes
1. **Git Hooks Disabled by Default**:
   - **What**: Local checkpoint generation via `post-commit` hooks is now **opt-in** (`install_git_hook = False` in `setup.py`).
   - **Action**: Push code to trigger checkpoints in CI/CD. To re-enable local hooks:
     ```bash
     python setup.py --install-git-hook
     ```
   - **Why**: Reduces local overhead and ensures consistency across environments.

2. **CLI Command Refactor**:
   - **Deprecated**: `--onboard` (bulk updates) and `--catchup` (now split into `--commit <hash>` and `--catchup-all`).
   - **New**:
     ```bash
     # Generate checkpoint for a specific commit
     python main.py --commit <sha>
     # Generate catchup summary (post-push)
     python main.py --catchup-all
     ```
   - **Impact**: Scripts using `--onboard` will fail. Update CI/CD pipelines and local aliases.

3. **CI/CD Dependency**:
   - Checkpoints are **only generated on push** (via `checkpoint.yml` GitHub Actions workflow).
   - **Risk**: Local commits won’t have checkpoints until pushed. Test critical changes in a branch before merging.

### ⚠️ High-Priority Updates
- **Merged Commit Exclusion**:
  The `checkpoint.yml` workflow now skips commits already merged to `main`/`master` using:
  ```bash
  git rev-list ${{ github.sha }} --not origin/main origin/master
  ```
  - **Impact**: Fewer redundant workflow runs, but ensure your branch is up-to-date with `main` to avoid missing context.

- **Storage Layer**:
  - Filename regex now supports **both legacy (`YYYY-MM-DD-hash.md`) and new formats (`Checkpoint-Author-YYYY-MM-DD-hash.md`)**.
  - **Action**: Validate custom scripts parsing checkpoint filenames.

---

## New Features & Additions
### 🌟 Multi-LLM Support (LiteLLM)
- **What**: Replaced Mistral-specific code with [LiteLLM](https://github.com/BerriAI/litellm), enabling **provider-agnostic LLM integration** (e.g., OpenAI, Anthropic, Hugging Face).
- **Files Modified**:
  - `llm_provider.py`: New abstraction layer.
  - `config/.checkpoint.yaml`: Centralized LLM settings.
- **Usage**:
  ```yaml
  # .checkpoint.yaml
  llm:
    provider: "openai"  # or "anthropic", "huggingface"
    model: "gpt-4-turbo"
  ```
  - **Action**: Update `config/.checkpoint.yaml` and test with your provider.

### ✨ Interactive Setup Wizard
- **What**: Pydantic-driven CLI wizard for:
  - Language detection (auto-configures parsers).
  - Git hook validation.
  - LLM provider setup.
- **Trigger**:
  ```bash
  python setup.py --interactive
  ```
- **Output**: Generates a validated `.checkpoint.yaml`.

### 📊 Commit-Granular Checkpoints
- **New**: Per-commit processing in CI/CD (`--commit <hash>`) replaces bulk `--onboard` updates.
- **Benefits**:
  - Finer-grained context (e.g., "This commit added X").
  - Reduced noise in catchup summaries.

---

## Refactors & Structural Changes
### 🔄 Git Hook Migration
| Change               | Before               | After                |
|----------------------|-----------------------|----------------------|
| **Hook Type**        | `post-commit`         | `pre-push`           |
| **Trigger**          | Every `git commit`    | Only on `git push`   |
| **CLI Command**      | `--onboard`           | `--commit <hash>`    |
| **Local Auto-Gen**   | Enabled by default    | Disabled (`opt-in`)  |

- **Rationale**: Reduces local friction and aligns with CI/CD-first workflows.

### 🗃️ Storage Layer Overhaul
1. **Regex-Based Parsing**:
   - Supports:
     - Legacy: `2026-01-13-abc123.md`
     - New: `Checkpoint-jane-2026-02-20-abc123.md`
   - **Graceful Degradation**: Skips malformed files instead of crashing.

2. **ChromaDB Cleanup**:
   - Removed binary artifacts; ensure `vector_db/` is reinitialized if using local embeddings.

### 📝 Centralized Configuration
- **New**: `.checkpoint.yaml` consolidates settings for:
  ```yaml
  git:
    hook: "pre-push"  # or "disabled"
  llm:
    provider: "litellm"
    model: "gpt-4-turbo"
  storage:
    format: "extended"  # or "legacy"
  ```
- **Deprecated**: Hardcoded values in `setup.py` and `main.py`.

---

## New Dependencies & Config Changes
### 📦 Dependencies
| Package       | Version  | Purpose                          |
|---------------|----------|----------------------------------|
| `litellm`     | `^1.4.0` | Multi-LLM provider abstraction  |
| `pydantic`    | `^2.5.0` | Config validation (setup wizard)|
| `gitpython`   | `^3.1.4` | Commit metadata parsing          |

- **Action**: Run `pip install -r requirements.txt` to update.

### ⚙️ Environment Variables
| Variable               | Default Value       | Purpose                          |
|------------------------|---------------------|----------------------------------|
| `CHECKPOINT_LLM_PROVIDER` | `litellm`          | Override YAML config             |
| `CHECKPOINT_GIT_HOOK`    | `disabled`         | Force-enable hooks locally       |
| `CHECKPOINT_DB_PATH`     | `./vector_db`      | Custom vector DB location        |

- **Example**:
  ```bash
  export CHECKPOINT_LLM_PROVIDER="openai"