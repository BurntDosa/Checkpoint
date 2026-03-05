import argparse
import sys
import subprocess
import os
from dotenv import load_dotenv
from src.config import load_config, get_api_key_for_provider

# Load environment variables from .env file
load_dotenv()

def check_api_key(config):
    """Check if API key is available for the configured provider."""
    api_key = get_api_key_for_provider(config.llm.provider)
    if not api_key:
        print(f"⚠️  Warning: No API key found for provider '{config.llm.provider}'")
        print(f"   Set the appropriate environment variable (e.g., MISTRAL_API_KEY, OPENAI_API_KEY)")
        print(f"   Or create a .env file with your API key")
        return False
    return True

def truncate_checkpoint(content: str, max_chars: int = 2000) -> str:
    """Truncate checkpoint content to reduce context size for LLM calls."""
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "\n\n[... truncated for brevity ...]\n"

def get_file_tree(path="."):
    """Simple wrapper to get file tree using `tree` or `find`."""
    try:
        # Try `tree` command first
        result = subprocess.run(["tree", "-L", "2", "-I", "__pycache__|venv|.git"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
    except FileNotFoundError:
        pass
    
    # Fallback to find
    try:
        result = subprocess.run(["find", ".", "-maxdepth", "2", "-not", "-path", "*/.*"], capture_output=True, text=True)
        return result.stdout
    except Exception:
        return "File structure unavailable."

def process_catchup(email, config, last_commit_info=None):
    """Helper to process catchup for a single email."""
    # Lazy imports to avoid loading heavy dependencies for setup commands
    from src.agents import CatchupGenerator
    from src.storage import get_checkpoints_since, save_catchup
    
    print(f"Generating Catchup Summary for user: {email}")
    
    # Use precomputed last_commit_info if available (performance optimization)
    if last_commit_info is None:
        from src.git_utils import get_last_commit_by_author
        last_commit = get_last_commit_by_author(email)
    else:
        last_commit = last_commit_info
    
    if not last_commit:
        print(f"  No commit history found for {email}. Skipping.")
        return
        
    print(f"  Last active: {last_commit['date']} (Commit: {last_commit['hash'][:8]})")
    
    checkpoints = get_checkpoints_since(last_commit['date'])
    if not checkpoints:
        print("  No checkpoints found since last activity.")
        return
        
    combined_content = "\n\n".join(checkpoints)
    
    generator = CatchupGenerator()
    result = generator(checkpoints_content=combined_content, user_last_active_date=str(last_commit['date']))
    
    if not result.summary_markdown:
        print(f"  Error: Failed to generate summary for {email} (LLM returned None).")
        return

    username = last_commit['author']
    filepath = save_catchup(result.summary_markdown, username, config.repository.output_dir)
    print(f"  Checkpoints updated: {filepath}")

def main():
    parser = argparse.ArgumentParser(
        description="Code Checkpoint - AI-powered git documentation and onboarding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  checkpoint init                    # Run setup wizard
  checkpoint --onboard               # Generate master context
  checkpoint --catchup               # Generate your catchup summary  
  checkpoint --commit abc123         # Analyze specific commit
  checkpoint config                  # Show current configuration
  checkpoint uninstall               # Remove git hook
        """
    )
    
    # Setup/config commands
    parser.add_argument("--init", action="store_true", help="Run interactive setup wizard")
    parser.add_argument("--config", action="store_true", help="Show current configuration")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall git hook")
    parser.add_argument("--install-hook", action="store_true", help="Install git hook")
    
    # Analysis commands
    parser.add_argument("--commit", help="Commit hash to analyze. Defaults to HEAD.", default=None)
    parser.add_argument("--dry-run", action="store_true", help="Print output instead of saving.")
    parser.add_argument("--onboard", action="store_true", help="Generate a Master Context map for new joinees.")
    parser.add_argument("--catchup", nargs='?', const=True, default=None, help="Generate a Catchup summary. If no email is provided, uses local git config user.email.")
    parser.add_argument("--catchup-all", action="store_true", help="Generate Catchup summaries for ALL active developers.")
    parser.add_argument("--pr", nargs=4, metavar=("PR_NUMBER", "BASE_REF", "HEAD_REF", "TITLE"),
                        help="Generate PR summary. Args: PR_NUMBER BASE_REF HEAD_REF TITLE")
    
    # Configuration file override
    parser.add_argument("--config-file", default=".checkpoint.yaml", help="Path to configuration file")
    
    args = parser.parse_args()
    
    # Handle setup/config commands first (don't need LLM config)
    if args.init:
        from src.setup import run_setup_wizard
        success = run_setup_wizard()
        sys.exit(0 if success else 1)
    
    if args.config:
        from src.setup import show_current_config
        show_current_config()
        sys.exit(0)
    
    if args.uninstall:
        from src.git_hook_installer import uninstall_hook
        success = uninstall_hook(".")
        sys.exit(0 if success else 1)
    
    if args.install_hook:
        from src.git_hook_installer import install_hook
        # Load config to respect auto_catchup setting
        config = load_config(args.config_file)
        success = install_hook(".", auto_catchup=config.features.auto_catchup)
        sys.exit(0 if success else 1)
    
    # Load configuration
    config = load_config(args.config_file)
    
    # Configure LLM using config
    # Check for API key before configuring LLM
    if not check_api_key(config):
        print("\n❌ Cannot proceed without API key. Please configure:")
        print("   1. Create a .env file in your repository root")
        print(f"   2. Add your API key: {config.llm.provider.upper()}_API_KEY=your_key_here")
        print("   3. Or run 'checkpoint --init' to configure interactively")
        sys.exit(1)
    
    try:
        from src.llm import configure_llm
        configure_llm(
            model=config.llm.model,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens
        )
    except Exception as e:
        print(f"❌ LLM Configuration Error: {e}")
        print("   Run 'checkpoint init' to configure.")
        sys.exit(1)
        
    try:
        # Lazy imports for analysis operations (avoid loading for setup commands)
        from src.agents import MasterContextGenerator
        from src.storage import list_checkpoints, save_master_context
        from src.mermaid_utils import generate_all_mermaid_diagrams

        # MODE 1: ONBOARDING (New Joinee)
        if args.onboard:
            print("Generating Master Context for New Joinee...")
            file_tree = get_file_tree()
            
            # Generate Mermaid Diagrams - choose method based on config
            if config.features.diagrams:
                from src.llm_diagrams import should_use_llm_diagrams, generate_diagrams_llm
                
                if should_use_llm_diagrams(config):
                    print("  Generating diagrams using LLM (language-agnostic)...")
                    dep_graph, class_hierarchy = generate_diagrams_llm(".", config.languages)
                else:
                    print("  Generating diagrams using AST parsing (Python)...")
                    dep_graph, class_hierarchy = generate_all_mermaid_diagrams(".", depth_limit=3)
            else:
                print("  Skipping diagram generation (disabled in config)")
                dep_graph = "Diagrams disabled in configuration"
                class_hierarchy = "Diagrams disabled in configuration"
            
            # Fetch last 5 checkpoints for context
            all_checkpoints = list_checkpoints()
            recent_content = ""
            for cp in all_checkpoints[-5:]: # Last 5
                with open(cp, "r", encoding="utf-8") as f:
                    # Truncate individual checkpoints to reduce context size
                    checkpoint_text = truncate_checkpoint(f.read(), max_chars=2000)
                    recent_content += f"--- Checkpoint: {cp.name} ---\n{checkpoint_text}\n\n"
                    
            generator = MasterContextGenerator()
            result = generator(
                file_structure=file_tree, 
                recent_checkpoints=recent_content,
                dependency_graph=dep_graph,
                class_hierarchy=class_hierarchy
            )
            
            # Handle None result
            if not result.master_markdown:
                print("Error: Failed to generate Master Context (LLM returned None).")
                return

            filepath = save_master_context(result.master_markdown, config.repository.master_context_file)
            print(f"Master Context updated: {filepath}")
            return

        # MODE 2: CATCHUP ALL (Automated Pipeline)
        if args.catchup_all:
            from src.git_utils import get_active_authors_with_last_commits
            import time
            
            print("Running Automated Catchup for ALL active developers...")
            # Single-pass optimization: get all authors + last commits at once
            author_map = get_active_authors_with_last_commits(days=60, max_count=1000)
            
            for i, (email, last_commit_info) in enumerate(author_map.items()):
                if i > 0:
                    print("Waiting 60s before next user to respect rate limits...")
                    time.sleep(60) 
                
                try:
                    process_catchup(email, config, last_commit_info=last_commit_info)
                except Exception as e:
                    print(f"  Error processing {email}: {e}")
            return

        # MODE 3: CATCHUP SINGLE (Manual)
        if args.catchup:
            from src.git_utils import get_local_user_email
            
            email = args.catchup
            
            # Auto-detect if flag is used without arg (const=True)
            if email is True:
                email = get_local_user_email()
                if not email:
                    print("Error: Could not detect local git user.email. Please provide it: --catchup your@email.com")
                    return
            
            process_catchup(email, config)
            return

        # MODE 4: PR SUMMARY
        if args.pr:
            from src.git_utils import get_diff_between_refs, get_commits_between_refs
            from src.agents import PRSummaryGenerator
            from src.storage import save_pr_summary

            pr_number, base_ref, head_ref, pr_title = args.pr
            print(f"Generating PR summary for PR #{pr_number}: {pr_title}")
            print(f"  Base: {base_ref} → Head: {head_ref}")

            # Get combined diff for all PR changes
            combined_diff = get_diff_between_refs(base_ref, head_ref)
            if not combined_diff.strip():
                print("No diff found between refs.")
                return

            # Get individual commits in the PR
            commits = get_commits_between_refs(base_ref, head_ref)
            print(f"  Found {len(commits)} commits in PR range")

            # Generate per-commit checkpoints and collect their content
            from src.git_utils import get_diff, get_commit_metadata
            from src.graph import app as graph_app

            commit_checkpoint_parts = []
            for commit_info in reversed(commits):  # chronological order
                commit_hash = commit_info["hash"]
                print(f"  Analyzing commit: {commit_hash[:8]} — {commit_info['message'][:60]}")
                try:
                    diff_content = get_diff(commit_hash)
                    if not diff_content.strip():
                        continue
                    metadata = get_commit_metadata(commit_hash)
                    initial_state = {
                        "diff_content": diff_content,
                        "commit_hash": commit_hash,
                        "metadata": metadata,
                        "generated_markdown": None,
                        "filepath": None
                    }
                    final_state = graph_app.invoke(initial_state, {"recursion_limit": 10})
                    if final_state and final_state.get("generated_markdown"):
                        commit_checkpoint_parts.append(
                            f"### Commit {commit_hash[:8]}: {commit_info['message']}\n\n"
                            + final_state["generated_markdown"]
                        )
                except Exception as e:
                    print(f"  Warning: Could not analyze commit {commit_hash[:8]}: {e}")

            commit_checkpoints = "\n\n---\n\n".join(commit_checkpoint_parts) if commit_checkpoint_parts else "No individual commit checkpoints available."

            # Determine branch name from head_ref (last path component for SHA fallback)
            head_branch = head_ref if "/" in head_ref or not head_ref.startswith("0" * 7) else head_ref

            generator = PRSummaryGenerator()
            result = generator(
                pr_title=pr_title,
                pr_number=pr_number,
                base_branch=base_ref,
                head_branch=head_branch,
                combined_diff=combined_diff[:8000],  # Truncate very large diffs
                commit_checkpoints=commit_checkpoints
            )

            if not result.pr_summary_markdown:
                print("Error: Failed to generate PR summary (LLM returned None).")
                return

            if args.dry_run:
                print("\n--- Generated PR Summary ---\n")
                print(result.pr_summary_markdown)
            else:
                filepath = save_pr_summary(
                    result.pr_summary_markdown,
                    pr_number,
                    head_branch,
                    config.repository.output_dir
                )
                print(f"PR summary saved to: {filepath}")
            return

        # MODE 5: STANDARD CHECKPOINT (Single Commit) - OPTIONAL / DEPRECATED DEFAULT
        # Only run if explicitly requested via flag (we can add --standard later if needed)
        # For now, we only want targeted docs (Onboard / Catchup) or explicit commit analysis.
        
        if args.commit:
            from src.git_utils import get_diff, get_commit_metadata
            from src.graph import app
            
            # If user explicitly asks for a commit analysis
            commit_hash = args.commit
            print(f"Analyzing commit: {commit_hash}")
            
            diff_content = get_diff(commit_hash)
            if not diff_content.strip():
                print("No changes found in diff.")
                return

            metadata = get_commit_metadata(commit_hash)
            
            initial_state = {
                "diff_content": diff_content,
                "commit_hash": commit_hash,
                "metadata": metadata,
                "generated_markdown": None,
                "filepath": None
            }
            
            final_state = app.invoke(initial_state, {"recursion_limit": 10})
            
            if final_state is None:
                 print("Error: Workflow failed to return state.")
                 return

            markdown_content = final_state.get("generated_markdown")
            if not markdown_content:
                print("No content generated.")
                return
                
            if args.dry_run:
                print("\n--- Generated Checkpoint ---\n")
                print(markdown_content)
            else:
                print(f"Checkpoint saved to: {final_state['filepath']}")
        else:
            # If no arguments provided, do nothing (or print help)
            if not (args.onboard or args.catchup or args.catchup_all):
                parser.print_help()
            
    except Exception as e:
        print(f"Error: {e}")
        # print traceback for debugging
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
