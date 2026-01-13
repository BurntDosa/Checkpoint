import os
import datetime
from pathlib import Path

CHECKPOINT_DIR = "checkpoints"

def ensure_checkpoint_dir():
    """Ensures the checkpoints directory exists."""
    Path(CHECKPOINT_DIR).mkdir(parents=True, exist_ok=True)

def save_checkpoint(content: str, commit_hash: str) -> str:
    """
    Saves the markdown content to a file.
    Format: YYYY-MM-DD-[commit_hash].md
    Returns the absolute path of the saved file.
    """
    ensure_checkpoint_dir()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}-{commit_hash}.md"
    file_path = os.path.join(CHECKPOINT_DIR, filename)
    
    with open(file_path, "w") as f:
        f.write(content)
        
    return os.path.abspath(file_path)

def list_checkpoints():
    """Lists all checkpoint files (standard commit checkpoints only)."""
    if not os.path.exists(CHECKPOINT_DIR):
        return []
    # Filter for standard checkpoints: YYYY-MM-DD-hash.md
    # Exclude Master Context and User Checkpoints
    all_files = Path(CHECKPOINT_DIR).glob("*.md")
    valid_checkpoints = []
    for f in all_files:
        if f.name.startswith("Checkpoint_") or f.name.startswith("catchup_") or f.name == "MASTER_CONTEXT.md":
            continue
        valid_checkpoints.append(f)
        
    return sorted(valid_checkpoints)

def get_checkpoints_since(since_date: datetime.datetime) -> list[str]:
    """
    Returns the get_checkpoints_since of all checkpoints created after the given date.
    Files are named YYYY-MM-DD-hash.md, but we should rely on file creation time or git date 
    if strictly needed. However, relying on filename date (YYYY-MM-DD) is decent for day-granularity.
    
    Better approach: Read file stats or metadata.
    """
    checkpoints = list_checkpoints()
    active_checkpoints = []
    
    for cp in checkpoints:
        # Extract date from filename: YYYY-MM-DD
        try:
            date_part = cp.name[:10]
            cp_date = datetime.datetime.strptime(date_part, "%Y-%m-%d")
            # Make cp_date timezone aware if needed, or naive. 
            # basic comparison: if cp_date >= date (ignoring time for filename based)
            # But the user might have committed at 10 AM and checkpoint at 11 AM same day.
            
            # Since filename only has day, this is imprecise.
            # Let's rely on file modification time? No, git checkout changes that.
            # We should probably store full timestamp in file or filenames.
            
            # For this MVP, we will perform a loose check: Checkpoints strictly AFTER the commit date.
            
            # Fix: Compare dates. 
            # Note: since_date from git is timezone aware.
            # Convert both to simple date for comparison or handle TZ.
            
            if cp_date.date() >= since_date.date():
                with open(cp, "r") as f:
                    active_checkpoints.append(f.read())
        except Exception:
            continue
            
    return active_checkpoints

def save_master_context(content: str) -> str:
    """Overwrites the MASTER_CONTEXT.md file in the root directory."""
    filename = "MASTER_CONTEXT.md" # Root level
    file_path = filename
    
    with open(file_path, "w") as f:
        f.write(content)
    return os.path.abspath(file_path)

def save_catchup(content: str, username: str) -> str:
    """Overwrites the user's catchup file in the checkpoints directory."""
    ensure_checkpoint_dir()
    # Sanitize username (replace spaces with _, remove weird chars)
    safe_username = "".join([c if c.isalnum() else "_" for c in username])
    filename = f"Checkpoint_{safe_username}.md"
    file_path = os.path.join(CHECKPOINT_DIR, filename)
    
    with open(file_path, "w") as f:
        f.write(content)
    return os.path.abspath(file_path)
