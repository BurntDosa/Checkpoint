"""LLM configuration using LiteLLM for universal provider support."""
import os
import dspy
from dotenv import load_dotenv
import litellm
import httpx


def configure_llm(model: str = None, api_key: str = None, temperature: float = 0.7,
                  max_tokens: int = 8000, **kwargs):
    """
    Configure LLM using LiteLLM for universal provider support.
    
    Supports OpenAI, Anthropic, Mistral, Azure, Ollama, and 100+ other providers.
    
    Args:
        model: Model name (e.g., "gpt-4", "claude-3-opus", "mistral-medium-2508")
        api_key: API key (optional, will try to load from environment)
        temperature: Temperature for generation (0.0-2.0)
        max_tokens: Maximum tokens to generate
        **kwargs: Additional parameters for LiteLLM
        
    Model naming examples:
        - "gpt-4" → OpenAI (needs OPENAI_API_KEY)
        - "claude-3-opus-20240229" → Anthropic (needs ANTHROPIC_API_KEY)
        - "mistral-medium-2508" → Mistral (needs MISTRAL_API_KEY)
        - "ollama/llama3" → Local Ollama (no API key needed)
    
    Returns:
        Configured DSPy LM instance
    """
    load_dotenv()
    
    # Use default model if not specified
    if model is None:
        model = os.getenv("LLM_MODEL", "mistral-medium-2508")
    
    # Set API key in environment if provided
    if api_key:
        provider = detect_provider_from_model(model)
        set_provider_api_key(provider, api_key)
    
    # Ensure model has provider prefix for LiteLLM
    # LiteLLM requires format like "mistral/model-name" for proper routing
    if "/" not in model:
        provider = detect_provider_from_model(model)
        if provider != "openai":  # OpenAI models work without prefix
            model = f"{provider}/{model}"
    
    # Disable SSL verification for corporate proxies (Zscaler, etc.)
    # For production environments, consider using proper certificate configuration
    litellm.client = httpx.Client(verify=False)
    
    # Configure LiteLLM settings
    litellm.drop_params = True  # Drop unsupported params instead of erroring
    litellm.set_verbose = False  # Reduce logging noise
    
    # Create DSPy LM instance with LiteLLM
    # DSPy v2.0+ has native LiteLLM support
    lm = dspy.LM(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )
    
    # Configure DSPy to use this LM
    dspy.settings.configure(lm=lm)
    
    return lm


def detect_provider_from_model(model: str) -> str:
    """
    Detect LLM provider from model name.
    
    Args:
        model: Model name
        
    Returns:
        Provider name (openai, anthropic, mistral, etc.)
    """
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
        # Default to openai for unknown models
        return "openai"


def set_provider_api_key(provider: str, api_key: str):
    """
    Set API key environment variable for a specific provider.
    
    Args:
        provider: Provider name
        api_key: API key value
    """
    provider_env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "google": "GOOGLE_API_KEY",
        "azure": "AZURE_API_KEY",
        "ollama": None,  # Ollama doesn't need API key
    }
    
    env_var = provider_env_map.get(provider.lower())
    if env_var:
        os.environ[env_var] = api_key


def configure_mistral():
    """
    Legacy function for backward compatibility.
    Configures Mistral using the new LiteLLM-based system.
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY environment variable is not set. Please add it to a .env file.")
    
    return configure_llm(model="mistral-medium-2508", api_key=api_key)
