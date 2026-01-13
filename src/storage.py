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
    """Lists all checkpoint files."""
    if not os.path.exists(CHECKPOINT_DIR):
        return []
    return sorted(list(Path(CHECKPOINT_DIR).glob("*.md")))
