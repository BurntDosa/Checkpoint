"""Configuration display utilities for Code Checkpoint."""
from checkpoint_agent.git_hook_installer import check_hook_status


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
    print(f"   Diagrams: {'yes' if config.features.diagrams else 'no'}")

    print(f"\nLanguages: {', '.join(config.languages)}")

    hook_status = check_hook_status(".")
    print(f"\nGit Hook Status:")
    print(f"   Installed: {'yes' if hook_status['hook_installed'] else 'no'}")
    print()
