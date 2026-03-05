# While You Were Gone — Since 2026-02-11
The default token limit for LLM configurations was increased from **2000 to 8000** in `src/llm.py` to reduce friction for use cases like code generation and multi-step reasoning. This is a **non-breaking change** but may impact cost/performance for teams relying on the previous default. No other updates were logged since your last activity.

---

## Critical Changes (Must-Read)
### Default Token Limit Increased in `configure_llm()`
- **What changed**: The `configure_llm()` function in `src/llm.py` now defaults `max_tokens=8000` (up from 2000).
- **Why it matters**:
  - **Cost/Performance**: Higher defaults may increase API latency and token usage costs. Audit your LLM calls if you enforce strict budgets.
  - **Assumptions**: Code assuming responses ≤2000 tokens (e.g., UI buffers, truncation logic) may need updates. Risk is low, as `max_tokens` was always overrideable.
- **Action required**:
  - Explicitly set `max_tokens=2000` in `configure_llm()` calls if you need the old behavior.
  - Review tests mocking LLM responses to ensure they handle longer outputs.

---

## New Features & Additions
*No new features or endpoints were added since 2026-02-11.*

---

## Refactors & Structural Changes
- The change to `configure_llm()` is isolated but touches a widely used utility. No architectural refactors or module reorganizations occurred.

---

## New Dependencies & Config Changes
*No new dependencies, environment variables, or configuration keys were added or modified.*

---

## Current Focus Areas
*No active focus areas or in-flight PRs were documented in this checkpoint.*

---