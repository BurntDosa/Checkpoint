"""Interactive setup wizard for Code Checkpoint."""
import getpass
from pathlib import Path
from checkpoint_agent.config import (
    CheckpointConfig, LLMConfig, RepositoryConfig, FeaturesConfig,
    write_config, set_api_key_env, validate_config, get_api_key_for_provider
)
from checkpoint_agent.git_hook_installer import install_hook, check_hook_status
from collections import Counter


def _select(prompt: str, choices: list, default: str = None) -> str:
    """Print numbered choices and return the selected value."""
    print(f"\n{prompt}")
    for i, choice in enumerate(choices, 1):
        marker = " (default)" if choice == default else ""
        print(f"  {i}. {choice}{marker}")
    default_idx = choices.index(default) + 1 if default in choices else 1
    raw = input(f"Enter number [{default_idx}]: ").strip()
    if not raw:
        return default if default else choices[0]
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(choices):
            return choices[idx]
    except ValueError:
        pass
    return default if default else choices[0]


def detect_languages(repo_path: str = ".") -> dict[str, float]:
    """
    Auto-detect programming languages from file extensions.

    Args:
        repo_path: Path to repository

    Returns:
        Dict mapping language name to percentage
    """
    path = Path(repo_path)

    # Language mapping
    ext_to_lang = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".java": "Java",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".php": "PHP",
        ".cpp": "C++",
        ".cc": "C++",
        ".c": "C",
        ".h": "C/C++",
        ".cs": "C#",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".R": "R",
    }

    # Count files by extension
    extension_counts = Counter()

    # Walk through all files (excluding common ignored dirs)
    ignore_dirs = {'.git', 'node_modules', 'venv', '__pycache__', 'build', 'dist', '.pytest_cache'}

    for file_path in path.rglob("*"):
        # Skip if in ignored directory
        if any(ignored in file_path.parts for ignored in ignore_dirs):
            continue

        if file_path.is_file() and file_path.suffix:
            extension_counts[file_path.suffix] += 1

    # Convert to languages
    language_counts = Counter()
    for ext, count in extension_counts.items():
        lang = ext_to_lang.get(ext)
        if lang:
            language_counts[lang] += count

    # Calculate percentages
    total = sum(language_counts.values())
    if total == 0:
        return {"Unknown": 100.0}

    percentages = {
        lang: round((count / total) * 100, 1)
        for lang, count in language_counts.most_common()
    }

    return percentages


def get_default_model_for_provider(provider: str) -> str:
    """Get default model name for a provider."""
    defaults = {
        "OpenAI": "gpt-4",
        "Anthropic": "claude-3-opus-20240229",
        "Mistral": "mistral-medium-2508",
        "Azure": "gpt-4",
        "Ollama": "ollama/llama3",
        "Google": "gemini-pro",
    }
    return defaults.get(provider, "gpt-4")


def run_setup_wizard() -> bool:
    """
    Run interactive setup wizard to configure Code Checkpoint.

    Returns:
        True if setup completed successfully, False otherwise
    """
    print("\n" + "="*60)
    print("Code Checkpoint Setup Wizard")
    print("="*60 + "\n")

    print("This wizard will help you configure Code Checkpoint for your repository.\n")

    # ==================== PHASE 1: LLM Configuration ====================
    print("Phase 1: LLM Configuration\n")

    provider = _select(
        "Select LLM provider:",
        choices=["OpenAI", "Anthropic", "Mistral", "Azure", "Ollama (Local)", "Google"],
        default="OpenAI"
    )

    if not provider:
        print("\nSetup cancelled.")
        return False

    # Get default model for provider
    default_model = get_default_model_for_provider(provider)

    model = input(f"Model name [{default_model}]: ").strip() or default_model

    # Get API key (skip for Ollama)
    api_key = None
    if provider != "Ollama (Local)":
        # Check if already in environment
        existing_key = get_api_key_for_provider(provider.lower())

        if existing_key:
            raw = input("Found existing API key in environment. Use it? [Y/n]: ").strip().lower()
            use_existing = raw in ("", "y", "yes")

            if use_existing:
                api_key = existing_key
            else:
                api_key = getpass.getpass(f"{provider} API Key: ")
        else:
            api_key = getpass.getpass(f"{provider} API Key: ")

        if not api_key:
            print("\nAPI key required. Setup cancelled.")
            return False

    # Temperature setting
    temp_raw = input("Temperature (0.0-2.0) [0.7]: ").strip()
    try:
        temperature = float(temp_raw) if temp_raw else 0.7
    except ValueError:
        temperature = 0.7

    # ==================== PHASE 2: Repository Configuration ====================
    print("\nPhase 2: Repository Configuration\n")

    output_dir = input("Checkpoint output directory [./checkpoints]: ").strip() or "./checkpoints"

    # Detect languages
    print("\nDetecting languages in repository...")
    detected_langs = detect_languages(".")

    if detected_langs:
        langs_str = ", ".join(f"{lang} ({pct}%)" for lang, pct in list(detected_langs.items())[:5])
        print(f"   Detected: {langs_str}")

        raw = input("Is this correct? [Y/n]: ").strip().lower()
        confirmed = raw in ("", "y", "yes")

        if not confirmed:
            default_langs = ", ".join(detected_langs.keys())
            manual_langs = input(f"Enter languages (comma-separated) [{default_langs}]: ").strip()
            if not manual_langs:
                manual_langs = default_langs

            if manual_langs:
                detected_langs = {lang.strip(): 0 for lang in manual_langs.split(",")}

    # ==================== Features Configuration ====================
    # Git hooks disabled by default - GitHub Actions generates checkpoints on push
    # Enable locally only for development/testing
    install_git_hook = False
    enable_diagrams = True
    auto_catchup = False  # Handled by GitHub Actions

    print("\nCore features enabled: Diagrams")
    print("   GitHub Actions generates checkpoints on push (no local git hooks)")

    # ==================== PHASE 3: Confirmation ====================
    print("\nConfiguration Summary")
    print("="*60)
    print(f"\nLLM:")
    print(f"   Provider: {provider}")
    print(f"   Model: {model}")
    print(f"   Temperature: {temperature}")

    print(f"\nRepository:")
    print(f"   Output Directory: {output_dir}")
    print(f"   Languages: {', '.join(detected_langs.keys())}")

    print(f"\nFeatures:")
    print(f"   Git Hook: {'yes' if install_git_hook else 'no'}")
    print(f"   Diagrams: {'yes' if enable_diagrams else 'no'}")
    print(f"   Auto Catchup: {'yes' if auto_catchup else 'no'}")
    print()

    raw = input("Proceed with this configuration? [Y/n]: ").strip().lower()
    proceed = raw in ("", "y", "yes")

    if not proceed:
        print("\nSetup cancelled.")
        return False

    # ==================== Create Configuration ====================
    print("\nWriting configuration...")

    # Create config object
    config = CheckpointConfig(
        llm=LLMConfig(
            provider=provider.lower().replace(" (local)", ""),
            model=model,
            temperature=temperature,
        ),
        repository=RepositoryConfig(
            output_dir=output_dir,
        ),
        features=FeaturesConfig(
            git_hook=install_git_hook,
            diagrams=enable_diagrams,
            auto_catchup=auto_catchup,
        ),
        languages=list(detected_langs.keys())
    )

    # Write config file
    if not write_config(config, ".checkpoint.yaml"):
        print("Failed to write configuration file.")
        return False

    # Save API key to .env if provided
    if api_key:
        try:
            set_api_key_env(provider.lower().replace(" (local)", ""), api_key)
            print("API key saved to .env file")
        except Exception as e:
            print(f"Warning: Could not save API key to .env: {e}")

    # Validate configuration
    is_valid, errors = validate_config(config)
    if not is_valid:
        print("\nConfiguration validation warnings:")
        for error in errors:
            print(f"   - {error}")

        raw = input("Continue anyway? [y/N]: ").strip().lower()
        continue_anyway = raw in ("y", "yes")

        if not continue_anyway:
            print("Setup cancelled.")
            return False

    # ==================== Install Git Hook ====================
    if install_git_hook:
        print("\nInstalling git hook...")
        if install_hook(".", auto_catchup=auto_catchup):
            print("Git hook installed successfully")
            if auto_catchup:
                print("   Auto-catchup enabled: summaries will be generated on each push")
        else:
            print("Git hook installation failed (you can install it later with 'checkpoint install-hook')")

    # ==================== Create Output Directory ====================
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        print(f"Created output directory: {output_dir}")
    except Exception as e:
        print(f"Could not create output directory: {e}")

    # ==================== Success! ====================
    print("\n" + "="*60)
    print("Setup Complete!")
    print("="*60)
    print("\nNext Steps:")
    print("   1. Generate master context:  checkpoint --onboard")
    print("   2. Generate your catchup:    checkpoint --catchup")
    print("   3. Make a commit:            git commit")
    print("      (Checkpoints will be auto-generated if hook is enabled)")
    print("\nDocumentation: https://github.com/checkpoint-agent/checkpoint#readme")
    print()

    return True


def show_current_config():
    """Display current configuration if it exists."""
    from checkpoint_agent.config import load_config

    config = load_config(".checkpoint.yaml")

    print("\n" + "="*60)
    print("Current Configuration")
    print("="*60)
    print(f"\nLLM:")
    print(f"   Provider: {config.llm.provider}")
    print(f"   Model: {config.llm.model}")
    print(f"   Temperature: {config.llm.temperature}")

    print(f"\nRepository:")
    print(f"   Output Directory: {config.repository.output_dir}")
    print(f"   Master Context File: {config.repository.master_context_file}")

    print(f"\nFeatures:")
    print(f"   Git Hook: {'yes' if config.features.git_hook else 'no'}")
    print(f"   Diagrams: {'yes' if config.features.diagrams else 'no'}")
    print(f"   Auto Catchup: {'yes' if config.features.auto_catchup else 'no'}")

    print(f"\nLanguages: {', '.join(config.languages)}")

    # Check git hook status
    hook_status = check_hook_status(".")
    print(f"\nGit Hook Status:")
    print(f"   Installed: {'yes' if hook_status['hook_installed'] else 'no'}")
    if hook_status['hook_installed']:
        print(f"   Executable: {'yes' if hook_status['hook_executable'] else 'no'}")
    print()
