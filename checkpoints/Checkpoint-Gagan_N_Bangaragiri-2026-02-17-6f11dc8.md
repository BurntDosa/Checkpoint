```markdown
# Code Checkpoint: Architectural Evolution (2026-02-17)

## Context
The **Code Checkpoint** system has undergone a **major transformation**, evolving from a Python-specific tool to a **language-agnostic developer onboarding platform**. This checkpoint summarizes the **architectural overhaul**, focusing on:
- **Git Hook Automation** (dev mode support),
- **Universal LLM Integration** (LiteLLM),
- **Metadata-Rich Storage**,
- **Interactive Setup**, and
- **Language-Agnostic Expansion**.

---

## Changes

### 1. Git Hook Installer: Development Mode
**Problem**: Hooks required a global `checkpoint` installation, blocking local development.
**Solution**:
- Added `repo_root` parameter to detect `.ven