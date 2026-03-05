import os
import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import re

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
        # Exclude Catchup files (Checkpoint_Username.md), PR summaries, and master context
        if f.name.startswith("Checkpoint_") or f.name.startswith("catchup_") or f.name.startswith("PR-") or f.name == "MASTER_CONTEXT.md":
            continue
            
        # Include Standard Checkpoints (Checkpoint-Username-Date-Hash.md or old format)
        valid_checkpoints.append(f)
        
    return sorted(valid_checkpoints)

def get_checkpoints_since(since_date: datetime.datetime) -> list[str]:
    """
    Returns the content of all checkpoints created after the given date.
    Handles both naming formats:
    - New: Checkpoint-Author-YYYY-MM-DD-hash.md
    - Old: YYYY-MM-DD-hash.md
    
    Optimized with parallel file reading for better I/O performance.
    """
    checkpoints = list_checkpoints()
    
    # Pattern to extract date (YYYY-MM-DD) from filename
    date_pattern = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
    
    # Filter by date first (cheap operation)
    valid_checkpoints = []
    for cp in checkpoints:
        try:
            filename = cp.name
            match = date_pattern.search(filename)
            if match:
                date_str = match.group(0)  # e.g., "2026-02-17"
                cp_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                if cp_date.date() >= since_date.date():
                    valid_checkpoints.append(cp)
        except Exception as e:
            # print(f"  Debug: Failed to parse date from {cp.name}: {e}")
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

def get_checkpoint_stats() -> dict:
    """
    Returns a summary of all checkpoint-related files in the checkpoints directory.

    Returns a dict with:
      - commit_checkpoints: count and date range of standard commit checkpoints
      - authors: unique author names extracted from checkpoint filenames
      - catchups: list of catchup usernames
      - pr_summaries: list of PR summary filenames
      - most_recent: list of the 5 most recent checkpoint filenames
    """
    if not os.path.exists(CHECKPOINT_DIR):
        return {
            "commit_checkpoints": {"count": 0, "oldest": None, "newest": None},
            "authors": [],
            "catchups": [],
            "pr_summaries": [],
            "most_recent": [],
        }

    all_files = sorted(Path(CHECKPOINT_DIR).glob("*.md"))
    date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})')
    # Checkpoint-AuthorName-YYYY-MM-DD-hash.md
    commit_pattern = re.compile(r'^Checkpoint-(.+)-(\d{4}-\d{2}-\d{2})-[0-9a-f]+\.md$')

    commit_files = []
    authors = set()
    catchups = []
    pr_summaries = []

    for f in all_files:
        name = f.name
        if name == "MASTER_CONTEXT.md":
            continue
        if name.startswith("Checkpoint_"):
            catchups.append(name[len("Checkpoint_"):-len(".md")])
        elif name.startswith("PR-"):
            pr_summaries.append(name)
        elif name.startswith("catchup_"):
            catchups.append(name)
        else:
            commit_files.append(name)
            m = commit_pattern.match(name)
            if m:
                authors.add(m.group(1))

    # Extract date range from commit checkpoint filenames
    dates = []
    for name in commit_files:
        m = date_pattern.search(name)
        if m:
            try:
                dates.append(datetime.datetime.strptime(m.group(1), "%Y-%m-%d").date())
            except ValueError:
                pass

    most_recent = sorted(commit_files)[-5:][::-1]

    return {
        "commit_checkpoints": {
            "count": len(commit_files),
            "oldest": str(min(dates)) if dates else None,
            "newest": str(max(dates)) if dates else None,
        },
        "authors": sorted(authors),
        "catchups": catchups,
        "pr_summaries": pr_summaries,
        "most_recent": most_recent,
    }

def save_pr_summary(content: str, pr_number: str, head_branch: str, output_dir: str = None) -> str:
    """
    Saves a PR summary to checkpoints/PR-{number}-{safe_branch}.md.

    Args:
        content: Markdown content to write
        pr_number: The pull request number
        head_branch: The feature branch name (used in filename)
        output_dir: Custom checkpoint directory (from config or default)

    Returns:
        Absolute path to saved file
    """
    checkpoint_dir = output_dir if output_dir else CHECKPOINT_DIR
    os.makedirs(checkpoint_dir, exist_ok=True)

    safe_branch = "".join([c if c.isalnum() or c in "-_" else "-" for c in head_branch])
    filename = f"PR-{pr_number}-{safe_branch}.md"
    file_path = os.path.join(checkpoint_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(file_path)

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

def save_catchup(content: str, email: str, checkpoint_dir: str = None) -> str:
    """
    Overwrites the user's catchup file in the checkpoints directory.
    Filename is derived from email (stable across author name changes).

    Args:
        content: Markdown content to write
        email: Git author email (used as stable filename key)
        checkpoint_dir: Custom checkpoint directory (from config or default)

    Returns:
        Absolute path to saved file
    """
    if checkpoint_dir is None:
        checkpoint_dir = CHECKPOINT_DIR

    os.makedirs(checkpoint_dir, exist_ok=True)

    # Use email as the stable filename key (replace non-alnum with _)
    safe_email = "".join([c if c.isalnum() else "_" for c in email])
    filename = f"Checkpoint_{safe_email}.md"
    file_path = os.path.join(checkpoint_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(file_path)
