"""Interactive setup wizard for Code Checkpoint."""
import questionary
from pathlib import Path
from src.config import (
    CheckpointConfig, LLMConfig, RepositoryConfig, FeaturesConfig,
    write_config, set_api_key_env, validate_config, get_api_key_for_provider
)
from src.git_hook_installer import install_hook, check_hook_status
from collections import Counter


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
    print("🚀 Code Checkpoint Setup Wizard")
    print("="*60 + "\n")
    
    print("This wizard will help you configure Code Checkpoint for your repository.\n")
    
    # ==================== PHASE 1: LLM Configuration ====================
    print("📦 Phase 1: LLM Configuration\n")
    
    provider = questionary.select(
        "Select LLM provider:",
        choices=[
            "OpenAI",
            "Anthropic",
            "Mistral",
            "Azure",
            "Ollama (Local)",
            "Google",
        ],
        default="OpenAI"
    ).ask()
    
    if not provider:
        print("\n❌ Setup cancelled.")
        return False
    
    # Get default model for provider
    default_model = get_default_model_for_provider(provider)
    
    model = questionary.text(
        f"Model name:",
        default=default_model,
        instruction=f"(Default: {default_model})"
    ).ask()
    
    if not model:
        model = default_model
    
    # Get API key (skip for Ollama)
    api_key = None
    if provider != "Ollama (Local)":
        # Check if already in environment
        existing_key = get_api_key_for_provider(provider.lower())
        
        if existing_key:
            use_existing = questionary.confirm(
                f"Found existing API key in environment. Use it?",
                default=True
            ).ask()
            
            if use_existing:
                api_key = existing_key
            else:
                api_key = questionary.password(
                    f"{provider} API Key:"
                ).ask()
        else:
            api_key = questionary.password(
                f"{provider} API Key:"
            ).ask()
        
        if not api_key:
            print("\n❌ API key required. Setup cancelled.")
            return False
    
    # Temperature setting
    temperature = questionary.text(
        "Temperature (0.0-2.0):",
        default="0.7",
        validate=lambda val: 0.0 <= float(val) <= 2.0 if val.replace('.', '').isdigit() else False
    ).ask()
    
    temperature = float(temperature) if temperature else 0.7
    
    # ==================== PHASE 2: Repository Configuration ====================
    print("\n📁 Phase 2: Repository Configuration\n")
    
    output_dir = questionary.path(
        "Checkpoint output directory:",
        default="./checkpoints",
        only_directories=True
    ).ask()
    
    if not output_dir:
        output_dir = "./checkpoints"
    
    # Detect languages
    print("\n🔍 Detecting languages in repository...")
    detected_langs = detect_languages(".")
    
    if detected_langs:
        langs_str = ", ".join(f"{lang} ({pct}%)" for lang, pct in list(detected_langs.items())[:5])
        print(f"   Detected: {langs_str}")
        
        confirmed = questionary.confirm(
            "Is this correct?",
            default=True
        ).ask()
        
        if not confirmed:
            # Manual language entry
            manual_langs = questionary.text(
                "Enter languages (comma-separated):",
                default=", ".join(detected_langs.keys())
            ).ask()
            
            if manual_langs:
                detected_langs = {lang.strip(): 0 for lang in manual_langs.split(",")}
    
    # ==================== All Features Enabled by Default ====================
    # All features are enabled by default for best experience
    install_git_hook = True
    enable_vector_db = True
    enable_diagrams = True
    auto_catchup = True
    
    print("\n✨ All features enabled: Git hooks, Vector DB, Diagrams, Auto-catchup")
    
    # ==================== PHASE 3: Confirmation ====================
    print("\n📋 Configuration Summary")
    print("="*60)
    print(f"\n🤖 LLM:")
    print(f"   Provider: {provider}")
    print(f"   Model: {model}")
    print(f"   Temperature: {temperature}")
    
    print(f"\n📁 Repository:")
    print(f"   Output Directory: {output_dir}")
    print(f"   Languages: {', '.join(detected_langs.keys())}")
    
    print(f"\n⚙️  Features:")
    print(f"   Git Hook: {'✅' if install_git_hook else '❌'}")
    print(f"   Vector DB: {'✅' if enable_vector_db else '❌'}")
    print(f"   Diagrams: {'✅' if enable_diagrams else '❌'}")
    print(f"   Auto Catchup: {'✅' if auto_catchup else '❌'}")
    print()
    
    proceed = questionary.confirm(
        "Proceed with this configuration?",
        default=True
    ).ask()
    
    if not proceed:
        print("\n❌ Setup cancelled.")
        return False
    
    # ==================== Create Configuration ====================
    print("\n⚙️  Writing configuration...")
    
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
            vector_db=enable_vector_db,
            diagrams=enable_diagrams,
            auto_catchup=auto_catchup,
        ),
        languages=list(detected_langs.keys())
    )
    
    # Write config file
    if not write_config(config, ".checkpoint.yaml"):
        print("❌ Failed to write configuration file.")
        return False
    
    # Save API key to .env if provided
    if api_key:
        try:
            set_api_key_env(provider.lower().replace(" (local)", ""), api_key)
            print("✅ API key saved to .env file")
        except Exception as e:
            print(f"⚠️  Warning: Could not save API key to .env: {e}")
    
    # Validate configuration
    is_valid, errors = validate_config(config)
    if not is_valid:
        print("\n⚠️  Configuration validation warnings:")
        for error in errors:
            print(f"   - {error}")
        
        continue_anyway = questionary.confirm(
            "Continue anyway?",
            default=False
        ).ask()
        
        if not continue_anyway:
            print("❌ Setup cancelled.")
            return False
    
    # ==================== Install Git Hook ====================
    if install_git_hook:
        print("\n🔗 Installing git hook...")
        if install_hook(".", auto_catchup=auto_catchup):
            print("✅ Git hook installed successfully")
            if auto_catchup:
                print("   📊 Auto-catchup enabled: summaries will be generated on each push")
        else:
            print("⚠️  Git hook installation failed (you can install it later with 'checkpoint install-hook')")
    
    # ==================== Create Output Directory ====================
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created output directory: {output_dir}")
    except Exception as e:
        print(f"⚠️  Could not create output directory: {e}")
    
    # ==================== Success! ====================
    print("\n" + "="*60)
    print("✨ Setup Complete!")
    print("="*60)
    print("\n📚 Next Steps:")
    print("   1. Generate master context:  checkpoint --onboard")
    print("   2. Generate your catchup:    checkpoint --catchup")
    print("   3. Make a commit:            git commit")
    print("      (Checkpoints will be auto-generated if hook is enabled)")
    print("\n📖 Documentation: https://github.com/checkpoint-agent/checkpoint#readme")
    print()
    
    return True


def show_current_config():
    """Display current configuration if it exists."""
    from src.config import load_config
    
    config = load_config(".checkpoint.yaml")
    
    print("\n" + "="*60)
    print("⚙️  Current Configuration")
    print("="*60)
    print(f"\n🤖 LLM:")
    print(f"   Provider: {config.llm.provider}")
    print(f"   Model: {config.llm.model}")
    print(f"   Temperature: {config.llm.temperature}")
    
    print(f"\n📁 Repository:")
    print(f"   Output Directory: {config.repository.output_dir}")
    print(f"   Master Context File: {config.repository.master_context_file}")
    print(f"   Vector DB Path: {config.repository.vector_db_path}")
    
    print(f"\n⚙️  Features:")
    print(f"   Git Hook: {'✅' if config.features.git_hook else '❌'}")
    print(f"   Vector DB: {'✅' if config.features.vector_db else '❌'}")
    print(f"   Diagrams: {'✅' if config.features.diagrams else '❌'}")
    print(f"   Auto Catchup: {'✅' if config.features.auto_catchup else '❌'}")
    
    print(f"\n🌐 Languages: {', '.join(config.languages)}")
    
    # Check git hook status
    hook_status = check_hook_status(".")
    print(f"\n🔗 Git Hook Status:")
    print(f"   Installed: {'✅' if hook_status['hook_installed'] else '❌'}")
    if hook_status['hook_installed']:
        print(f"   Executable: {'✅' if hook_status['hook_executable'] else '❌'}")
    print()
