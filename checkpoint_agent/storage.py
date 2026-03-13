import os
import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import re

CHECKPOINT_DIR = "checkpoints"
CATCHUP_DIR = "catchups"

INITIAL_MASTER_CONTEXT_TEMPLATE = """\
# Master Context

> Auto-generated onboarding document for **{repo_name}**. Created {date}.

This document is a living architectural overview of the codebase. It is regenerated
automatically when pull requests are merged, so its content always reflects the
current state of the project.

**This is a placeholder.** The sections below will be populated with real analysis
after meaningful code changes are merged.

## Architecture Overview
_Will be populated automatically._

## Key Decision Log
_Will be populated automatically._

## Gotchas & Tech Debt
_Will be populated automatically._

## Dependency Map
_Will be populated automatically._

## Getting Started
_Will be populated automatically._
"""

def ensure_checkpoint_dir():
    """Ensures the checkpoints directory exists."""
    Path(CHECKPOINT_DIR).mkdir(parents=True, exist_ok=True)

def save_checkpoint(content: str, commit_hash: str, author: str = None) -> str:
    """
    Saves the markdown content to a stable per-author file, prepending the new
    commit entry so the file grows as a living document (newest first).
    Format: Checkpoint-[AuthorName].md
    Returns the absolute path of the saved file.
    """
    ensure_checkpoint_dir()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    short_hash = commit_hash[:7]

    safe_author = "".join([c if c.isalnum() else "_" for c in author]) if author else "unknown"
    filename = f"Checkpoint-{safe_author}.md"
    file_path = os.path.join(CHECKPOINT_DIR, filename)

    # Wrap new content with a commit header
    entry = f"## Commit `{short_hash}` — {date_str}\n\n{content.strip()}"

    # Prepend to existing content so newest is always at the top
    existing = ""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            existing = f.read().strip()

    with open(file_path, "w", encoding="utf-8") as f:
        if existing:
            f.write(entry + "\n\n---\n\n" + existing + "\n")
        else:
            f.write(entry + "\n")

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
    Returns content of all checkpoint files. Since each file is a stable
    per-author living document (newest first), the full content is returned
    and the LLM filters by the since_date passed in the prompt.
    """
    checkpoints = list_checkpoints()

    def read_file(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    with ThreadPoolExecutor(max_workers=10) as executor:
        contents = list(executor.map(read_file, checkpoints))

    return [c for c in contents if c]

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
    # Stable per-author format: Checkpoint-AuthorName.md
    commit_pattern = re.compile(r'^Checkpoint-(.+)\.md$')

    commit_files = []
    authors = set()
    catchups = []
    pr_summaries = []

    for f in all_files:
        name = f.name
        if name == "MASTER_CONTEXT.md":
            continue
        if name.startswith("Checkpoint_"):
            # Legacy catchup files in checkpoints/ dir
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

    # Also scan the new catchups/ directory
    catchup_dir = Path(CATCHUP_DIR)
    if catchup_dir.exists():
        for f in catchup_dir.glob("*.md"):
            if f.name.startswith("Catchup_"):
                catchups.append(f.name[len("Catchup_"):-len(".md")])

    # Extract date range from commit checkpoint file contents
    dates = []
    for name in commit_files:
        try:
            fp = Path(CHECKPOINT_DIR) / name
            text = fp.read_text(encoding="utf-8", errors="ignore")
            for m in date_pattern.finditer(text):
                try:
                    dates.append(datetime.datetime.strptime(m.group(1), "%Y-%m-%d").date())
                except ValueError:
                    pass
        except Exception:
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

def ensure_catchup_dir(catchup_dir: str = None):
    """Ensures the catchups directory exists."""
    Path(catchup_dir or CATCHUP_DIR).mkdir(parents=True, exist_ok=True)


def get_catchup_path(email: str, catchup_dir: str = None) -> str:
    """Returns the path to the user's catchup file (may not exist yet)."""
    if catchup_dir is None:
        catchup_dir = CATCHUP_DIR
    safe_email = "".join([c if c.isalnum() else "_" for c in email])
    return os.path.join(catchup_dir, f"Catchup_{safe_email}.md")


def get_existing_catchup(email: str, catchup_dir: str = None) -> str | None:
    """Read and return the existing catchup content for a user, or None."""
    path = get_catchup_path(email, catchup_dir)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass
    return None


def save_catchup(content: str, email: str, catchup_dir: str = None) -> str:
    """
    Overwrites the user's catchup file in the catchups directory.
    Filename is derived from email (stable across author name changes).

    Args:
        content: Markdown content to write
        email: Git author email (used as stable filename key)
        catchup_dir: Custom catchup directory (from config or default)

    Returns:
        Absolute path to saved file
    """
    if catchup_dir is None:
        catchup_dir = CATCHUP_DIR

    ensure_catchup_dir(catchup_dir)

    safe_email = "".join([c if c.isalnum() else "_" for c in email])
    filename = f"Catchup_{safe_email}.md"
    file_path = os.path.join(catchup_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(file_path)


def delete_catchup(email: str, catchup_dir: str = None) -> bool:
    """
    Deletes the catchup file for a user (e.g. when they commit and are caught up).

    Args:
        email: Git author email
        catchup_dir: Custom catchup directory (from config or default)

    Returns:
        True if a file was deleted, False if no file existed
    """
    path = get_catchup_path(email, catchup_dir)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
