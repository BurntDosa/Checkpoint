import git
from typing import Optional

def get_repo(path: str = ".") -> git.Repo:
    return git.Repo(path, search_parent_directories=True)

def get_diff(commit_hash: str, repo_path: str = ".") -> str:
    """
    Retrieves the diff for a specific commit.
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
        diff_text += str(d) + "\n"
        
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

def get_active_authors(days: int = 60, repo_path: str = ".") -> list[str]:
    """
    Returns a list of unique emails of authors who have committed in the last N days.
    """
    repo = get_repo(repo_path)
    # Calculate cutoff date
    import datetime
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
    
    active_emails = set()
    for commit in repo.iter_commits():
        if commit.committed_datetime.replace(tzinfo=None) < cutoff_date:
            break
        if commit.author.email:
            active_emails.add(commit.author.email)
            
    return list(active_emails)
