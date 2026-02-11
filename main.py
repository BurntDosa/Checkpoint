import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from src.graph import app
from src.git_utils import get_diff, get_commit_metadata, get_current_commit_hash, get_active_authors_with_last_commits
from src.agents import CatchupGenerator, MasterContextGenerator
from src.storage import get_checkpoints_since, list_checkpoints, save_master_context, save_catchup
from src.llm import configure_mistral
import subprocess
from src.mermaid_utils import generate_all_mermaid_diagrams

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

def process_catchup(email, last_commit_info=None):
    """Helper to process catchup for a single email."""
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
    filepath = save_catchup(result.summary_markdown, username)
    print(f"  Checkpoints updated: {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Code Checkpoint Generator")
    parser.add_argument("--commit", help="Commit hash to analyze. Defaults to HEAD.", default=None)
    parser.add_argument("--dry-run", action="store_true", help="Print output instead of saving.")
    parser.add_argument("--onboard", action="store_true", help="Generate a Master Context map for new joinees.")
    parser.add_argument("--catchup", nargs='?', const=True, default=None, help="Generate a Catchup summary. If no email is provided, uses local git config user.email.")
    parser.add_argument("--catchup-all", action="store_true", help="Generate Catchup summaries for ALL active developers.")
    
    args = parser.parse_args()
    
    # Ensure env is configured
    try:
        configure_mistral()
    except Exception as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)
        
    try:

        # MODE 1: ONBOARDING (New Joinee)
        if args.onboard:
            print("Generating Master Context for New Joinee...")
            file_tree = get_file_tree()
            
            # Generate Mermaid Diagrams in parallel (50% faster)
            print("  Generating diagrams (parallel)...")
            dep_graph, class_hierarchy = generate_all_mermaid_diagrams(".", depth_limit=3)
            
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

            filepath = save_master_context(result.master_markdown)
            print(f"Master Context updated: {filepath}")
            return

        # MODE 2: CATCHUP ALL (Automated Pipeline)
        if args.catchup_all:
            print("Running Automated Catchup for ALL active developers...")
            # Single-pass optimization: get all authors + last commits at once
            author_map = get_active_authors_with_last_commits(days=60, max_count=1000)
            import time
            
            for i, (email, last_commit_info) in enumerate(author_map.items()):
                if i > 0:
                    print("Waiting 60s before next user to respect rate limits...")
                    time.sleep(60) 
                
                try:
                    process_catchup(email, last_commit_info=last_commit_info)
                except Exception as e:
                    print(f"  Error processing {email}: {e}")
            return

        # MODE 3: CATCHUP SINGLE (Manual)
        if args.catchup:
            email = args.catchup
            
            # Auto-detect if flag is used without arg (const=True)
            if email is True:
                from src.git_utils import get_local_user_email
                email = get_local_user_email()
                if not email:
                    print("Error: Could not detect local git user.email. Please provide it: --catchup your@email.com")
                    return
            
            process_catchup(email)
            return

        # MODE 4: STANDARD CHECKPOINT (Single Commit) - OPTIONAL / DEPRECATED DEFAULT
        # Only run if explicitly requested via flag (we can add --standard later if needed)
        # For now, we only want targeted docs (Onboard / Catchup) or explicit commit analysis.
        
        if args.commit:
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
