# While You Were Gone — Since 2026-02-11 11:13:07+05:30
You missed a **major architectural overhaul** and **repository migration**. The project has **dropped DSPy for LiteLLM**, simplified documentation, removed unstable features (ChromaDB, semantic search), and shifted to GitHub Actions as the primary workflow. The repository is now maintained under **BurntDosa/Checkpoint** with new metadata. **Critical**: Your local code, tests, and CI/CD will break until updated.

---

## Critical Changes (Must-Read)
### 1. **DSPy → LiteLLM Migration (Breaking)**
   - **Files**: `checkpoint_agent/agents.py`, `checkpoint_agent/llm.py`
   - **Impact**:
     - All `dspy.Signature`/`dspy.Module` classes **deleted**. Agents are now flat classes with `__call__` methods using raw prompt strings.
     - Return types changed from `dspy.Prediction` to `types.SimpleNamespace`.
     - `configure_llm()` no longer returns an object; it sets a module-level `_llm_config` dict.
   - **Action Required**:
     - Replace all `dspy` imports with `from types import SimpleNamespace`.
     - Update tests to mock `litellm.completion` instead of `dspy.predictor.forward`.
     - Remove `dspy-ai` from dependencies (`pip uninstall dspy-ai`).

### 2. **GitHub Actions Workflow Fixes (Breaking)**
   - **File**: `.github/workflows/checkpoint.yml`
   - **Impact**:
     - `--catchup-skip` now accepts **comma-separated emails** (e.g., `--catchup-skip "dev1@company.com,dev2@company.com"`).
     - File staging bug fixed: `git add checkpoints/` replaces the old glob pattern.
   - **Action Required**:
     - Update CI/CD scripts to pass multiple emails to `--catchup-skip`.
     - Verify workflows use `git add checkpoints/` (not `git add checkpoints/Checkpoint_*.md`).

### 3. **Repository Migration (Metadata Only)**
   - **File**: `pyproject.toml`
   - **Impact**:
     - All GitHub links (homepage, docs, repo, issues) now point to [`BurntDosa/Checkpoint`](https://github.com/BurntDosa/Checkpoint).
     - Maintainer email updated to `gagan.bangaragiri@gmail.com`.
   - **Action Required**:
     - Update CI/CD pipelines referencing the old repo (`checkpoint-agent/checkpoint`).
     - Verify `pip show checkpoint-agent` reflects the new metadata.

### 4. **ChromaDB and Semantic Search Removed (Breaking)**
   - **Files**: `checkpoint_agent/agents.py`, `README.md`
   - **Impact**:
     - `vector_db_path`, `ignore_patterns`, and `file_patterns` config keys **removed**.
     - `CheckpointGenerator` no longer writes to ChromaDB.
   - **Action Required**:
     - Remove ChromaDB-related config from `.checkpoint.yaml`.
     - Migrate to alternative search tools if needed.

### 5. **Git Hooks Deprecated (Non-Breaking but Urgent)**
   - **Files**: `git_hook_installer.py`, `.checkpoint.yaml`
   - **Impact**:
     - Hooks are **disabled by default** (`git_hook: false`).
     - Primary workflow is now GitHub Actions (`--install-ci`).
   - **Action Required**:
     - Run `checkpoint --install-ci` to migrate to GitHub Actions.
     - Opt into hooks via `.checkpoint.yaml` if still needed:
       ```yaml
       features:
         git_hook: true
       ```

---

## New Features & Additions
### 1. **LiteLLM Provider Flexibility**
   - **Files**: `checkpoint_agent/llm.py`
   - **Details**:
     - Supports **provider-agnostic model strings** (e.g., `"groq/llama3-70b"`, `"mistral/mistral-small"`).
     - Uses `drop_params=True` to ignore unsupported args (e.g., `top_p` for Mistral).
   - **Usage**:
     ```python
     configure_llm(model="groq/llama3-70b")  # No code changes needed for new providers
     ```

### 2. **Multi-Committer Support in GitHub Actions**
   - **File**: `.github/workflows/checkpoint.yml`
   - **Details**:
     - Extracts **all unique author emails** in a push range and skips them via `--catchup-skip`.
     - Fixes redundant catchups for teams with multiple committers per push.
   - **Example**:
     ```bash
     SKIP_EMAILS=$(git log --format='%ae' ${{ github.event.before }}..${{ github.sha }} | sort -u | tr '\n' ',' | sed 's/,$//')
     checkpoint --catchup-all --catchup-skip "$SKIP_EMAILS"
     ```

### 3. **Simplified CLI for CI Setup**
   - **File**: `checkpoint_agent/__main__.py`
   - **Details**:
     - New command: `--install-ci` auto-generates a GitHub Actions workflow file.
     - `--stats` command shows checkpoint metrics (e.g., files generated, time taken).
   - **Usage**:
     ```bash
     checkpoint --install-ci  # Sets up GitHub Actions
     checkpoint --stats        # Shows metrics
     ```

### 4. **LLM-Driven Diagrams**
   - **File**: `llm_diagrams.py`
   - **Details**:
     - Replaced AST-based Mermaid diagrams with **LLM-generated diagrams** (simpler, supports non-Python languages).
   - **Tradeoff**: Less precise for complex Python codebases but more universal.

### 5. **Prompt Guardrails**
   - **Files**: `checkpoint_agent/agents.py`
   - **Details**:
     - Catchup templates now include **anti-hallucination disclaimers**:
       ```markdown
       IMPORTANT: Only include information explicitly stated in the checkpoints.
       Do not invent team member names, owners, PR numbers, or work items.
       ```

---

## Refactors & Structural Changes
### 1. **Documentation Overhaul**
   - **File**: `README.md` (complete rewrite)
   - **Changes**:
     - **Leads with outcomes**: `MASTER_CONTEXT.md` (onboarding) and `checkpoints/Checkpoint_<email>.md` (catchup).
     - **Removed**: ChromaDB, semantic search, LangGraph, and "The Map"/"The News Feed" metaphors.
     - **Added**:
       - Table of GitHub Actions triggers (push/PR/merge → outputs).
       - Clear separation between **local** (`--onboard`) and **CI** (`--install-ci`) workflows.
     - **Simplified setup**: `pip install checkpoint-agent` (no `-e .`).

### 2. **Agent Code Simplification**
   - **File**: `checkpoint_agent/agents.py`
   - **Changes**:
     - **Before**: 520 lines (DSPy abstractions).
     - **After**: 160 lines (raw LiteLLM calls).
     - **Example Refactor**:
       ```python
       # OLD (DSPy):
       class CheckpointGenerator(dspy.Module):
           def __init__(self):
               super().__init__()
               self.generate = dspy.ChainOfThought(UnifiedCheckpointSignature)

       # NEW (LiteLLM):
       class CheckpointGenerator:
           def __call__(self, input_data: dict) -> SimpleNamespace:
               response = _call_llm(system_prompt="...", user_prompt=f"...{input_data['diff']}...")
               return SimpleNamespace(markdown_content=response["choices"][0]["message"]["content"])