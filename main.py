import argparse
import sys
from src.graph import app
from src.git_utils import get_diff, get_commit_metadata, get_current_commit_hash

def main():
    parser = argparse.ArgumentParser(description="Code Checkpoint Generator")
    parser.add_argument("--commit", help="Commit hash to analyze. Defaults to HEAD.", default=None)
    parser.add_argument("--dry-run", action="store_true", help="Print output instead of saving.")
    
    args = parser.parse_args()
    
    try:
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
        sys.exit(1)

if __name__ == "__main__":
    main()
