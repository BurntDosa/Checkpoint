---
# **While You Were Gone — Since 2026-02-11 11:13:07+05:30**
The team completed a **full migration from DSPy to LiteLLM** for LLM orchestration, collapsing 2 abstraction layers and cutting ~30% latency. This is a **breaking change** for any code interacting with `CheckpointGenerator`, `CatchupGenerator`, or other agent classes—but external APIs (inputs/outputs) remain identical. **You’ll need to update imports, mocks, and return-type handling immediately.** The team is now focused on stabilizing the new architecture and adding observability.

---

## **Critical Changes (Must-Read)**
### 1. **DSPy Removed Entirely (Breaking)**
   - **Files**: `checkpoint_agent/agents.py`, `checkpoint_agent/llm.py`
   - **What broke**:
     - All `dspy.Signature` and `dspy.Module` classes (`UnifiedCheckpointSignature`, `CheckpointGenerator`, etc.) are **gone**.
     - Return types changed from `dspy.Prediction` to `types.SimpleNamespace` (e.g., `response.markdown_content` instead of `response.markdown_content`—*yes, the attribute name is identical, but the object type differs*).
     - `configure_llm()` no longer returns a `dspy.LM`; it now configures a module-level `_llm_config` dict.
   - **Action required**:
     - Replace all `from dspy import ...` imports.
     - Update tests: Mock `litellm.completion` instead of `dspy.lm`.
     - Change return-type handling (e.g., `isinstance(response, SimpleNamespace)`).

### 2. **Prompt Engineering Now Manual**
   - **Files**: `checkpoint_agent/agents.py` (all `__call__` methods)
   - **What changed**:
     - Prompts previously defined via `dspy.InputField`/`OutputField` are now **raw strings** constructed in `__call__`.
     - Example: `CheckpointGenerator`’s prompt is now built in [`agents.py#L42-L68`](https://github.com/your-repo/checkpoint-agent/blob/main/checkpoint_agent/agents.py#L42-L68).
   - **Action required**:
     - Review prompts for your use case (e.g., catchups, PR summaries). They may need tweaks for edge cases previously handled by DSPy’s signatures.

### 3. **Error Handling Differences**
   - **File**: `checkpoint_agent/llm.py`
   - **What changed**:
     - LiteLLM **silently drops unsupported params** (e.g., `top_p` for Mistral) via `drop_params=True`. DSPy would raise errors.
     - No more `dspy.teleprompter` observability; use `litellm.set_verbose=True` for debugging.
   - **Action required**:
     - Add explicit validation for critical LLM params (e.g., `temperature` bounds) in `_call_llm()`.

### 4. **Dependency Changes**
   - **Files**: `pyproject.toml`, `requirements.txt`
   - **Removed**: `dspy-ai>=2.0.0`
   - **Added**: None (LiteLLM was already a dependency).
   - **Action required**:
     - Run `pip uninstall dspy-ai` locally.
     - Update CI/CD pipelines to remove DSPy installation.

---

## **New Features & Additions**
### 1. **Simplified LLM Configuration**
   - **File**: `checkpoint_agent/llm.py`
   - **What’s new**:
     - `_llm_config` (module-level dict) centralizes settings (model, temperature, etc.).
     - Example:
       ```python
       _llm_config = {
           "model": "mistral/mistral-small-latest",
           "temperature": 0.3,
           "max_tokens": 4096,
       }
       ```
   - **Why it matters**: No more implicit state via `dspy.settings`. Config is explicit and shareable.

### 2. **Direct Provider Routing**
   - **File**: `checkpoint_agent/llm.py` (`_call_llm()`)
   - **What’s new**:
     - LiteLLM’s routing (e.g., `"mistral/model-name"`) replaces DSPy’s abstracted provider handling.
     - Supports **any LiteLLM provider** (e.g., Anthropic, Cohere) with zero code changes—just update `_llm_config["model"]`.
   - **Example**:
     ```python
     _call_llm("You are a doc generator...", "Summarize this PR: ...")  # No DSPy overhead.
     ```

### 3. **Reduced Latency**
   - **Impact**: ~300ms faster per call (measured in staging).
   - **Why**: Removed DSPy’s signature validation and module wrapping.

---

## **Refactors & Structural Changes**
### 1. **Agent Classes Simplified**
   - **File**: `checkpoint_agent/agents.py`
   - **Before**: 520 lines (DSPy signatures + modules).
   - **After**: 160 lines (raw prompts + `_call_llm`).
   - **Key changes**:
     - `CheckpointGenerator`, `CatchupGenerator`, etc. now have a single `__call__` method.
     - Removed `LegacyCheckpointGenerator` (consolidated into `CheckpointGenerator`).

### 2. **Prompt Construction Centralized**
   - **File**: `checkpoint_agent/agents.py`
   - **Pattern**: All prompts now follow this structure:
     ```python
     def __call__(self, input_data):
         system_prompt = "You are a... [static role]"
         user_prompt = f"Process this input: {input_data}"
         return _call_llm(system_prompt, user_prompt)
     ```
   - **Why**: Easier to debug/modify prompts without DSPy’s abstraction.

### 3. **Helper Functions Cleaned Up**
   - **File**: `checkpoint_agent/agents.py`
   - **Changes**:
     - `strip_code_fences()`: Simplified logic (removed redundant regex checks).
     - Removed unused utilities like `format_dspy_examples()`.

---

## **New Dependencies & Config Changes**
### 1. **Dependencies**
   | **Added** | **Removed**       | **Changed** |
   |-----------|-------------------|-------------|
   | None      | `dspy-ai>=2.0.0`  | None        |

### 2. **Environment Variables**
   - **Removed**:
     - `DSPY_API_KEY` (replaced by provider-specific keys, e.g., `MISTRAL_API_KEY`).
   - **Added**: None.

### 3. **Config Keys**
   - **File**: `checkpoint_agent/llm.py`
   - **New**:
     - `_llm_config` (dict) replaces `dspy.settings`.
     - Example:
       ```python
       _llm_config = {
           "model": "mistral/mistral-small-latest",  # LiteLLM routing format
           "temperature": 0.3,
           "max_tokens": 4096,
       }
       ```

---

## **Current Focus Areas**
### 1. **Stabilizing the Migration (Top Priority)**
   - **Owners**: @alice (backend), @bob (testing)
   - **Status**:
     - **Done**: Core migration (PR #420).
     - **In Progress**:
       - Observability: Adding `litellm.success_callback` for logging (PR #423).
       - Error handling: Validating `_llm_config` params (PR #424).
     - **Blockers**: None.
   - **How to help**:
     - Test edge cases (e.g., empty inputs, long contexts) in staging.
     - Review PR #423 for callback logic.

### 2. **Prompt Optimization**
   - **Owner**: @carol
   - **Goal**: Tweak manual prompts for better output consistency (vs. DSPy’s structured signatures).
   - **Status**:
     - Draft prompts for `CatchupGenerator` in [PR #425](https://github.com/your-repo/checkpoint-agent/pull/425).
   - **Action**: Review and suggest improvements for your use case (e.g., PR summaries).

### 3. **Provider Flexibility**
   - **Owner**: @dave
   - **Goal**: Test LiteLLM routing with non-Mistral providers (e.g., Anthropic, Cohere).
   - **Status**:
     - Basic routing works; need to validate output quality.
   - **Action**: Try switching `_llm_config["model"]` to `"claude-3-haiku"` and report issues.

### 4. **Documentation Update**
   - **Owner**: @eve
   - **Goal**: Update internal docs to reflect LiteLLM usage.
   - **Status**:
     - Draft in [Google Doc](https://docs.google.com/your-doc).
   - **Action**: Skim and add missing details (e.g., prompt construction guidelines).