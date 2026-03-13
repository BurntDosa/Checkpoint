import git
import re
from typing import Optional
from functools import lru_cache

@lru_cache(maxsize=1)
def get_repo(path: str = ".") -> git.Repo:
    return git.Repo(path, search_parent_directories=True)

# Files that belong to the checkpoint system itself — never send to the LLM
_CHECKPOINT_SYSTEM_PATTERNS = re.compile(
    r'^('
    r'\.checkpoint\.yaml'
    r'|\.github/workflows/checkpoint\.yml'
    r'|checkpoints/'
    r'|catchups/'
    r'|MASTER_CONTEXT\.md'
    r')'
)


def _is_checkpoint_system_file(path: str) -> bool:
    """Return True if the path belongs to the checkpoint system, not the user's project."""
    return bool(_CHECKPOINT_SYSTEM_PATTERNS.match(path)) if path else False


def get_diff(commit_hash: str, repo_path: str = ".") -> str:
    """
    Retrieves the diff for a specific commit.
    Excludes checkpoint system files (.checkpoint.yaml, workflow, checkpoints/, MASTER_CONTEXT.md)
    so the LLM only sees the project's actual code changes.
    """
    repo = get_repo(repo_path)
    commit = repo.commit(commit_hash)
    # Diff against parent
    if commit.parents:
        parent = commit.parents[0]
        diff = parent.diff(commit, create_patch=True)
    else:
        # First commit
        diff = commit.diff(git.NULL_TREE, create_patch=True)

    diff_text = ""
    for d in diff:
        # Skip checkpoint system files
        if _is_checkpoint_system_file(d.a_path) or _is_checkpoint_system_file(d.b_path):
            continue
        if d.diff:
            diff_text += d.diff.decode('utf-8', errors='replace') + "\n"

    return diff_text

def get_current_commit_hash(repo_path: str = ".") -> str:
    repo = get_repo(repo_path)
    return repo.head.commit.hexsha

def get_commit_metadata(commit_hash: str, repo_path: str = ".") -> dict:
    repo = get_repo(repo_path)
    commit = repo.commit(commit_hash)
    return {
        "author": commit.author.name,
        "email": commit.author.email,
        "date": commit.committed_datetime.isoformat(),
        "message": commit.message.strip()
    }

def get_last_commit_by_author(email: str, repo_path: str = ".") -> Optional[dict]:
    """Finds the last commit metadata for a specific author email."""
    repo = get_repo(repo_path)
    # Search entire history
    for commit in repo.iter_commits():
        if commit.author.email == email:
            return {
                "hash": commit.hexsha,
                "date": commit.committed_datetime, # Keep as datetime object for comparison
                "message": commit.message.strip(),
                "author": commit.author.name
            }
    return None

def get_local_user_email(repo_path: str = ".") -> Optional[str]:
    """Retrieves the email of the current local git user."""
    repo = get_repo(repo_path)
    reader = repo.config_reader()
    return reader.get_value("user", "email", default=None)

# Emails to exclude from catchup generation (bots, CI agents)
BOT_EMAILS = {
    "agent@codecheckpoint.local",
    "noreply@github.com",
    "github-actions[bot]@users.noreply.github.com",
}

def get_active_authors_with_last_commits(days: int = 60, repo_path: str = ".", max_count: int = 1000) -> dict[str, dict]:
    """
    Single-pass optimization: Returns dict mapping email -> last commit info.
    Replaces the O(n²) pattern of get_active_authors() + get_last_commit_by_author().
    Bot emails (CI agents) are excluded automatically.

    Args:
        days: Look back this many days
        repo_path: Path to repository
        max_count: Maximum commits to scan (limits history depth)

    Returns:
        {email: {"hash": str, "date": datetime, "message": str, "author": str}}
    """
    repo = get_repo(repo_path)
    import datetime
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)

    author_map = {}

    for commit in repo.iter_commits(max_count=max_count):
        if commit.committed_datetime.replace(tzinfo=None) < cutoff_date:
            break

        email = commit.author.email
        if not email or email in BOT_EMAILS or email in author_map:
            continue

        # First time seeing this human author = their most recent commit
        author_map[email] = {
            "hash": commit.hexsha,
            "date": commit.committed_datetime,
            "message": commit.message.strip(),
            "author": commit.author.name
        }

    return author_map

def get_current_branch(repo_path: str = ".") -> str:
    """Returns the name of the currently active branch."""
    repo = get_repo(repo_path)
    return repo.active_branch.name

def get_diff_between_refs(base_ref: str, head_ref: str, repo_path: str = ".") -> str:
    """
    Returns the combined git diff between two refs (branches, SHAs, tags).
    Excludes checkpoint system files. Useful for generating a full PR diff.
    """
    repo = get_repo(repo_path)
    # Use pathspec to exclude checkpoint system files
    return repo.git.diff(
        base_ref, head_ref,
        "--", ".", ":!.checkpoint.yaml", ":!.github/workflows/checkpoint.yml",
        ":!checkpoints/", ":!catchups/", ":!MASTER_CONTEXT.md",
    )

def get_commits_between_refs(base_ref: str, head_ref: str, repo_path: str = ".") -> list[dict]:
    """
    Returns a list of commit metadata dicts for commits reachable from head_ref but not base_ref.
    Each dict has: hash, author, email, date, message.
    """
    repo = get_repo(repo_path)
    commits = []
    for commit in repo.iter_commits(f"{base_ref}..{head_ref}"):
        commits.append({
            "hash": commit.hexsha,
            "author": commit.author.name,
            "email": commit.author.email,
            "date": commit.committed_datetime.isoformat(),
            "message": commit.message.strip()
        })
    return commits
