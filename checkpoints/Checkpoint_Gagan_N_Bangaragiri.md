# While You Were Gone

## Changes Summary
- **Git Hooks**: Now support **development mode**—detects local `.venv` and runs `main.py` directly, eliminating global install friction.
- **Universal LLM Support**: Replaced Mistral with **LiteLLM**, adding compatibility for OpenAI, Anthropic, Azure, Ollama, and more.
- **Interactive Setup**: New wizard guides users through config (language detection, API keys, feature toggles).
- **Git Integration**: Hooks auto-generate checkpoints on commit; includes backup/restoration.
- **Language-Agnostic**: Expanded beyond Python with LLM-based diagram generation and multi-language support.

## New Dependencies
- **Core**: `litellm` (LLM abstraction), `pydantic` (config models).
- **Dev Mode**: Virtualenv (`.venv/bin/python`) for local hook execution.
- **Packaging**: `pyproject.toml` for standardized distribution.

## Refactors
- **Decoupled LLM Logic**: LiteLLM integration replaces hardcoded Mistral calls.
- **Dynamic Hooks**: Templates now use f-strings to inject commands based on environment (dev vs. global).
- **Modular Config**: Pydantic models manage settings (API keys, paths, toggles).

## Current Focus
- **Testing**: Validate LLM provider integrations (e.g., OpenAI vs. Ollama) and git hook reliability.
- **Expansion**: Adding more language-specific features (e.g., JavaScript/TypeScript support).
- **Documentation**: Updating diagrams and examples for new setup workflows.