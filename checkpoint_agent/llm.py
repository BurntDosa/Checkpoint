"""LLM configuration using LiteLLM for universal provider support."""
import os
from dotenv import load_dotenv
import litellm
import httpx

# Module-level config used by agents.py
_llm_config: dict = {
    "model": "mistral/mistral-medium-2508",
    "temperature": 0.7,
    "max_tokens": 8000,
}


def configure_llm(model: str = None, api_key: str = None, temperature: float = 0.7,
                  max_tokens: int = 8000, **kwargs):
    """
    Configure LLM using LiteLLM for universal provider support.

    Supports OpenAI, Anthropic, Mistral, Azure, Ollama, and 100+ other providers.

    Model naming examples:
        - "gpt-4" → OpenAI (needs OPENAI_API_KEY)
        - "claude-3-opus-20240229" → Anthropic (needs ANTHROPIC_API_KEY)
        - "mistral-medium-2508" → Mistral (needs MISTRAL_API_KEY)
        - "ollama/llama3" → Local Ollama (no API key needed)
    """
    global _llm_config
    load_dotenv()

    if model is None:
        model = os.getenv("LLM_MODEL", "mistral-medium-2508")

    if api_key:
        provider = detect_provider_from_model(model)
        set_provider_api_key(provider, api_key)

    # Ensure model has provider prefix for LiteLLM routing
    if "/" not in model:
        provider = detect_provider_from_model(model)
        if provider != "openai":  # OpenAI models work without prefix
            model = f"{provider}/{model}"

    # Optionally disable SSL verification for corporate proxies (Zscaler, etc.)
    if os.getenv("CHECKPOINT_SSL_VERIFY", "true").lower() == "false":
        litellm.client = httpx.Client(verify=False)
    litellm.drop_params = True
    litellm.set_verbose = False

    _llm_config = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    return _llm_config


def detect_provider_from_model(model: str) -> str:
    """Detect LLM provider from model name."""
    model_lower = model.lower()

    if "gpt" in model_lower or "o1" in model_lower:
        return "openai"
    elif "claude" in model_lower:
        return "anthropic"
    elif "mistral" in model_lower:
        return "mistral"
    elif "gemini" in model_lower or "palm" in model_lower:
        return "google"
    elif "ollama/" in model_lower:
        return "ollama"
    elif "azure" in model_lower:
        return "azure"
    else:
        return "openai"


def set_provider_api_key(provider: str, api_key: str):
    """Set API key environment variable for a specific provider."""
    provider_env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "google": "GOOGLE_API_KEY",
        "azure": "AZURE_API_KEY",
        "ollama": None,
    }
    env_var = provider_env_map.get(provider.lower())
    if env_var:
        os.environ[env_var] = api_key
