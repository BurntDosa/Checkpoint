import os
import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

CHECKPOINT_DIR = "checkpoints"

def ensure_checkpoint_dir():
    """Ensures the checkpoints directory exists."""
    Path(CHECKPOINT_DIR).mkdir(parents=True, exist_ok=True)

def save_checkpoint(content: str, commit_hash: str, author: str = None) -> str:
    """
    Saves the markdown content to a file.
    Format: Checkpoint-[AuthorName]-[YYYY-MM-DD]-[short_hash].md
    Returns the absolute path of the saved file.
    """
    ensure_checkpoint_dir()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    short_hash = commit_hash[:7]
    
    # Sanitize Author Name
    if author:
        safe_author = "".join([c if c.isalnum() else "_" for c in author])
        filename = f"Checkpoint-{safe_author}-{date_str}-{short_hash}.md"
    else:
        filename = f"{date_str}-{commit_hash}.md" # Fallback
        
    file_path = os.path.join(CHECKPOINT_DIR, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return os.path.abspath(file_path)

def list_checkpoints():
    """Lists all checkpoint files (standard commit checkpoints only)."""
    if not os.path.exists(CHECKPOINT_DIR):
        return []
    # Filter for standard checkpoints: Checkpoint-[Author]-[Date]-[Hash].md OR Old format YYYY-MM-DD-hash.md
    # Exclude User Catchup Checkpoints: Checkpoint_[Author].md (Underscore separator for catchups)
    
    all_files = Path(CHECKPOINT_DIR).glob("*.md")
    valid_checkpoints = []
    for f in all_files:
        # Exclude Catchup files (Checkpoint_Username.md)
        if f.name.startswith("Checkpoint_") or f.name.startswith("catchup_") or f.name == "MASTER_CONTEXT.md":
            continue
            
        # Include Standard Checkpoints (Checkpoint-Username-Date-Hash.md or old format)
        valid_checkpoints.append(f)
        
    return sorted(valid_checkpoints)

def get_checkpoints_since(since_date: datetime.datetime) -> list[str]:
    """
    Returns the content of all checkpoints created after the given date.
    Files are named YYYY-MM-DD-hash.md, but we should rely on file creation time or git date 
    if strictly needed. However, relying on filename date (YYYY-MM-DD) is decent for day-granularity.
    
    Optimized with parallel file reading for better I/O performance.
    """
    checkpoints = list_checkpoints()
    
    # Filter by date first (cheap operation)
    valid_checkpoints = []
    for cp in checkpoints:
        try:
            date_part = cp.name[:10]
            cp_date = datetime.datetime.strptime(date_part, "%Y-%m-%d")
            if cp_date.date() >= since_date.date():
                valid_checkpoints.append(cp)
        except Exception:
            continue
    
    # Parallel file reading with UTF-8 encoding
    def read_file(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        active_checkpoints = list(executor.map(read_file, valid_checkpoints))
    
    return [content for content in active_checkpoints if content]

def save_master_context(content: str, filename: str = "MASTER_CONTEXT.md") -> str:
    """
    Overwrites the MASTER_CONTEXT.md file (or custom filename) in the root directory.
    
    Args:
        content: Markdown content to write
        filename: Filename to use (from config or default)
        
    Returns:
        Absolute path to saved file
    """
    file_path = filename
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(file_path)

def save_catchup(content: str, username: str, checkpoint_dir: str = None) -> str:
    """
    Overwrites the user's catchup file in the checkpoints directory.
    
    Args:
        content: Markdown content to write
        username: Username from git
        checkpoint_dir: Custom checkpoint directory (from config or default)
        
    Returns:
        Absolute path to saved file
    """
    if checkpoint_dir is None:
        checkpoint_dir = CHECKPOINT_DIR
    
    # Ensure directory exists
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Sanitize username (replace spaces with _, remove weird chars)
    safe_username = "".join([c if c.isalnum() else "_" for c in username])
    filename = f"Checkpoint_{safe_username}.md"
    file_path = os.path.join(checkpoint_dir, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(file_path)
