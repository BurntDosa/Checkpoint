"""Configuration management for Code Checkpoint."""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: str = Field(default="mistral", description="LLM provider name")
    model: str = Field(default="mistral-medium-2508", description="Model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=8000, gt=0)
    api_key_env: str = Field(default="", description="Environment variable name for API key")


class RepositoryConfig(BaseModel):
    """Repository-specific configuration."""
    output_dir: str = Field(default="./checkpoints", description="Checkpoint output directory")
    master_context_file: str = Field(default="MASTER_CONTEXT.md", description="Master context filename")
    vector_db_path: str = Field(default=".chroma_db", description="ChromaDB storage path")
    ignore_patterns: list[str] = Field(
        default_factory=lambda: ["node_modules", "venv", ".git", "build", "dist", "__pycache__"],
        description="Directories to ignore during analysis"
    )
    file_patterns: list[str] = Field(
        default_factory=lambda: ["**/*.py", "**/*.js", "**/*.ts", "**/*.java", "**/*.go", "**/*.rs"],
        description="File patterns to analyze"
    )


class FeaturesConfig(BaseModel):
    """Feature toggles."""
    git_hook: bool = Field(default=False, description="Install git hook (not needed if using GitHub Actions)")
    vector_db: bool = Field(default=True, description="Enable ChromaDB semantic search")
    diagrams: bool = Field(default=True, description="Generate Mermaid diagrams")
    auto_catchup: bool = Field(default=False, description="Auto-generate catchup (handled by GitHub Actions)")


class CheckpointConfig(BaseModel):
    """Complete checkpoint configuration."""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    repository: RepositoryConfig = Field(default_factory=RepositoryConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    languages: list[str] = Field(
        default_factory=lambda: ["python"],
        description="Detected/configured languages"
    )


def get_default_config() -> CheckpointConfig:
    """Get default configuration."""
    return CheckpointConfig()


def load_config(config_path: str = ".checkpoint.yaml") -> CheckpointConfig:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        CheckpointConfig instance with loaded or default settings
    """
    path = Path(config_path)
    
    if not path.exists():
        print(f"⚠️  Config file {config_path} not found. Using defaults.")
        return get_default_config()
    
    try:
        with open(path, 'r') as f:
            data = yaml.safe_load(f) or {}
        
        config = CheckpointConfig(**data)
        return config
    except Exception as e:
        print(f"⚠️  Error loading config: {e}. Using defaults.")
        return get_default_config()


def write_config(config: CheckpointConfig, config_path: str = ".checkpoint.yaml") -> bool:
    """
    Write configuration to YAML file.
    
    Args:
        config: CheckpointConfig instance
        config_path: Path to write config file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        path = Path(config_path)
        data = config. model_dump(mode='python')
        
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Configuration written to {config_path}")
        return True
    except Exception as e:
        print(f"❌ Error writing config: {e}")
        return False


def validate_config(config: CheckpointConfig) -> tuple[bool, list[str]]:
    """
    Validate configuration for common issues.
    
    Args:
        config: CheckpointConfig instance
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Check output directory parent exists
    output_dir = Path(config.repository.output_dir)
    if not output_dir.parent.exists():
        errors.append(f"Parent directory of output_dir does not exist: {output_dir.parent}")
    
    # Check if API key is set (load from env)
    api_key = get_api_key_for_provider(config.llm.provider)
    if not api_key:
        errors.append(f"API key not found for provider '{config.llm.provider}'. Set appropriate environment variable.")
    
    # Check temperature range (Pydantic should catch this, but double-check)
    if not 0.0 <= config.llm.temperature <= 2.0:
        errors.append(f"Temperature must be between 0.0 and 2.0, got {config.llm.temperature}")
    
    return len(errors) == 0, errors


def get_api_key_for_provider(provider: str) -> Optional[str]:
    """
    Get API key from environment for a specific provider.
    
    Args:
        provider: Provider name (openai, anthropic, mistral, etc.)
        
    Returns:
        API key string or None if not found
    """
    # Map provider names to common environment variable names
    provider_env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "azure": "AZURE_API_KEY",
        "ollama": None,  # Ollama typically doesn't need API key
    }
    
    # Normalize provider name
    provider_lower = provider.lower()
    
    # Get env var name
    env_var = provider_env_map.get(provider_lower)
    if env_var is None:
        # For Ollama or unknown providers, might not need API key
        return os.getenv("API_KEY")  # Generic fallback
    
    return os.getenv(env_var)


def set_api_key_env(provider: str, api_key: str):
    """
    Set API key in environment for a specific provider.
    
    Args:
        provider: Provider name
        api_key: API key value
    """
    provider_env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "azure": "AZURE_API_KEY",
    }
    
    provider_lower = provider.lower()
    env_var = provider_env_map.get(provider_lower, "API_KEY")
    
    os.environ[env_var] = api_key
    
    # Also write to .env file for persistence
    env_path = Path(".env")
    env_lines = []
    
    # Read existing .env if present
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_lines = f.readlines()
    
    # Update or add the API key
    key_found = False
    for i, line in enumerate(env_lines):
        if line.startswith(f"{env_var}="):
            env_lines[i] = f"{env_var}={api_key}\n"
            key_found = True
            break
    
    if not key_found:
        env_lines.append(f"{env_var}={api_key}\n")
    
    # Write back
    with open(env_path, 'w') as f:
        f.writelines(env_lines)
