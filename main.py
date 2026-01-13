import argparse
import sys
from src.graph import app
from src.git_utils import get_diff, get_commit_metadata, get_current_commit_hash, get_last_commit_by_author
from src.agents import CatchupGenerator, MasterContextGenerator
from src.storage import get_checkpoints_since, list_checkpoints, save_master_context, save_catchup
from src.llm import configure_gemini
import subprocess

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

def main():
    parser = argparse.ArgumentParser(description="Code Checkpoint Generator")
    parser.add_argument("--commit", help="Commit hash to analyze. Defaults to HEAD.", default=None)
    parser.add_argument("--dry-run", action="store_true", help="Print output instead of saving.")
    parser.add_argument("--onboard", action="store_true", help="Generate a Master Context map for new joinees.")
    parser.add_argument("--catchup", nargs='?', const=True, default=None, help="Generate a Catchup summary. If no email is provided, uses local git config user.email.")
    
    args = parser.parse_args()
    
    # Ensure env is configured
    try:
        configure_gemini()
    except Exception as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)
        
    try:
        # MODE 1: ONBOARDING (New Joinee)
        if args.onboard:
            print("Generating Master Context for New Joinee...")
            file_tree = get_file_tree()
            # Fetch last 5 checkpoints for context
            all_checkpoints = list_checkpoints()
            recent_content = ""
            for cp in all_checkpoints[-5:]: # Last 5
                with open(cp, "r") as f:
                    recent_content += f"--- Checkpoint: {cp.name} ---\n{f.read()}\n\n"
                    
            generator = MasterContextGenerator()
            result = generator(file_structure=file_tree, recent_checkpoints=recent_content)
            
            filepath = save_master_context(result.master_markdown)
            print(f"Master Context updated: {filepath}")
            return

        # MODE 2: CATCHUP (Returning Developer)
        if args.catchup:
            email = args.catchup
            
            # Auto-detect if flag is used without arg (const=True)
            if email is True:
                from src.git_utils import get_local_user_email
                email = get_local_user_email()
                if not email:
                    print("Error: Could not detect local git user.email. Please provide it: --catchup your@email.com")
                    return
            
            print(f"Generating Catchup Summary for user: {email}")
            last_commit = get_last_commit_by_author(email)
            
            if not last_commit:
                print(f"No commit history found for {email}. Treating as a new user? Try --onboard.")
                return
                
            print(f"Last active: {last_commit['date']} (Commit: {last_commit['hash'][:8]})")
            
            checkpoints = get_checkpoints_since(last_commit['date'])
            if not checkpoints:
                print("No checkpoints found since your last activity. You are up to date!")
                return
                
            combined_content = "\n\n".join(checkpoints)
            
            generator = CatchupGenerator()
            result = generator(checkpoints_content=combined_content, user_last_active_date=str(last_commit['date']))
            
            filepath = save_catchup(result.summary_markdown, email)
            print(f"Catchup summary updated: {filepath}")
            return

        # MODE 3: STANDARD CHECKPOINT (Single Commit)
        commit_hash = args.commit if args.commit else get_current_commit_hash()
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
        
        # Invoke the LangGraph workflow
        # Note: In a real run, we'd need the API key set.
        # Use recursion_limit purely as safety
        final_state = app.invoke(initial_state, {"recursion_limit": 10})
        
        if args.dry_run:
            print("\n--- Generated Checkpoint ---\n")
            print(final_state["generated_markdown"])
        else:
            print(f"Checkpoint saved to: {final_state['filepath']}")
            
    except Exception as e:
        print(f"Error: {e}")
        # print traceback for debugging
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
