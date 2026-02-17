"""Git hook installation and management."""
import os
import shutil
import stat
from pathlib import Path
from typing import Optional


def get_prepush_hook_template(auto_catchup: bool = False, repo_root: Optional[Path] = None) -> str:
    """
    Generate pre-push hook template that generates checkpoints for commits being pushed.
    
    Args:
        auto_catchup: Whether to auto-generate catchup summaries
        repo_root: Repository root path for detecting dev mode
        
    Returns:
        Hook script content
    """
    # Detect if we're in development mode (main.py exists in repo root)
    checkpoint_cmd = "checkpoint"
    if repo_root and (repo_root / "main.py").exists():
        # Development mode - use direct Python execution
        venv_python = repo_root / ".venv" / "bin" / "python"
        main_py = repo_root / "main.py"
        if venv_python.exists() and main_py.exists():
            checkpoint_cmd = f'"{venv_python}" "{main_py}"'
    
    hook = f"""#!/bin/sh
# Code Checkpoint Auto-generated Pre-Push Hook
# This hook generates checkpoints for commits being pushed

# Read stdin (remote name and URL)
while read local_ref local_sha remote_ref remote_sha
do
    if [ "$local_sha" = "0000000000000000000000000000000000000000" ]; then
        # Branch is being deleted, skip
        continue
    fi
    
    if [ "$remote_sha" = "0000000000000000000000000000000000000000" ]; then
        # New branch, get all commits
        RANGE="$local_sha"
    else
        # Existing branch, get commits between remote and local
        RANGE="$remote_sha..$local_sha"
    fi
    
    # Get list of commits being pushed
    COMMITS=$(git rev-list "$RANGE" 2>/dev/null)
    
    if [ -n "$COMMITS" ]; then
        echo "Generating checkpoints for commits being pushed..."
        
        # Generate checkpoint for each commit
        for commit in $COMMITS; do
            echo "  Processing commit: $commit"
            {checkpoint_cmd} --commit "$commit" >> .checkpoint.log 2>&1
        done
        
"""
    
    if auto_catchup:
        hook += f"""        # Generate catchup summaries
        echo "Generating catchup summaries..."
        {checkpoint_cmd} --catchup-all >> .checkpoint.log 2>&1
        
"""
    
    hook += """        echo "✅ Checkpoints generated successfully"
    fi
done

exit 0
"""
    
    return hook


def find_git_root(start_path: str = ".") -> Optional[Path]:
    """
    Find the git repository root directory.
    
    Args:
        start_path: Starting directory to search from
        
    Returns:
        Path to .git directory or None if not found
    """
    current = Path(start_path).resolve()
    
    # Traverse up the directory tree
    while current != current.parent:
        git_dir = current / ".git"
        if git_dir.exists():
            return git_dir
        current = current.parent
    
    return None


def check_existing_hook(git_dir: Path, hook_name: str = "post-commit") -> tuple[bool, Optional[str]]:
    """
    Check if a git hook already exists.
    
    Args:
        git_dir: Path to .git directory
        hook_name: Name of the hook to check
        
    Returns:
        Tuple of (exists, content) where content is None if hook doesn't exist
    """
    hook_path = git_dir / "hooks" / hook_name
    
    if not hook_path.exists():
        return False, None
    
    try:
        with open(hook_path, 'r') as f:
            content = f.read()
        return True, content
    except Exception as e:
        print(f"⚠️  Error reading existing hook: {e}")
        return True, None


def backup_existing_hook(git_dir: Path, hook_name: str = "post-commit") -> bool:
    """
    Backup an existing git hook.
    
    Args:
        git_dir: Path to .git directory
        hook_name: Name of the hook to backup
        
    Returns:
        True if backup successful or no backup needed, False on error
    """
    hook_path = git_dir / "hooks" / hook_name
    
    if not hook_path.exists():
        return True  # No backup needed
    
    backup_path = git_dir / "hooks" / f"{hook_name}.checkpoint-backup"
    
    try:
        shutil.copy2(hook_path, backup_path)
        print(f"✅ Backed up existing hook to {backup_path.name}")
        return True
    except Exception as e:
        print(f"❌ Error backing up hook: {e}")
        return False


def make_executable(file_path: Path) -> bool:
    """
    Make a file executable.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if os.name == 'nt':  # Windows
            # Create .bat wrapper for Windows
            bat_path = file_path.with_suffix('.bat')
            bat_content = f"@echo off\nsh {file_path.name}\n"
            with open(bat_path, 'w') as f:
                f.write(bat_content)
            print(f"✅ Created Windows wrapper: {bat_path.name}")
        else:  # Unix/Mac
            # Add execute permission
            current_mode = file_path.stat().st_mode
            file_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return True
    except Exception as e:
        print(f"❌ Error making hook executable: {e}")
        return False


def install_hook(repo_path: str = ".", force: bool = False, auto_catchup: bool = False) -> bool:
    """
    Install pre-push git hook for automatic checkpoint generation.
    
    Checkpoints are generated only when commits are pushed, not on every local commit.
    Uses a composition pattern: if an existing hook is found, it's backed up.
    
    Args:
        repo_path: Path to git repository
        force: If True, overwrite existing checkpoint hook
        auto_catchup: If True, include auto-catchup in hook
        
    Returns:
        True if installation successful, False otherwise
    """
    # Find git directory first to get repo root
    git_dir = find_git_root(repo_path)
    if not git_dir:
        print("❌ Not a git repository. Run 'git init' first.")
        return False
    
    # Get repository root (parent of .git directory)
    repo_root = git_dir.parent
    
    # Generate hook template based on config and repo root
    hook_template = get_prepush_hook_template(auto_catchup, repo_root)
    
    hooks_dir = git_dir / "hooks"
    hook_path = hooks_dir / "pre-push"
    
    # Ensure hooks directory exists
    hooks_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if existing hook exists
    exists, existing_content = check_existing_hook(git_dir, "pre-push")
    
    if exists and existing_content:
        # Check if it's already our hook
        if "Code Checkpoint Auto-generated Pre-Push Hook" in existing_content:
            if not force:
                print("✅ Checkpoint hook already installed.")
                return True
            else:
                print("♻️  Reinstalling checkpoint hook...")
        
        # Check if it's a user hook (not ours)
        if "Code Checkpoint" not in existing_content:
            print(f"⚠️  Existing {hook_path.name} hook detected.")
            
            # Backup the existing hook
            if not backup_existing_hook(git_dir, "pre-push"):
                print("❌ Failed to backup existing hook. Aborting.")
                return False
            
            # Compose: append our hook to existing
            composed_content = existing_content.rstrip() + "\n\n" + hook_template
            
            try:
                with open(hook_path, 'w') as f:
                    f.write(composed_content)
                print("✅ Composed checkpoint hook with existing hook.")
            except Exception as e:
                print(f"❌ Error writing composed hook: {e}")
                return False
        else:
            # It's our hook, just overwrite
            try:
                with open(hook_path, 'w') as f:
                    f.write(hook_template)
            except Exception as e:
                print(f"❌ Error writing hook: {e}")
                return False
    else:
        # No existing hook, create fresh
        try:
            with open(hook_path, 'w') as f:
                f.write(hook_template)
            print("✅ Installed checkpoint pre-push hook.")
        except Exception as e:
            print(f"❌ Error creating hook: {e}")
            return False
    
    # Make executable
    if not make_executable(hook_path):
        return False
    
    print(f"✅ Hook installed at {hook_path}")
    print("   Checkpoints will be generated automatically when you push commits.")
    if auto_catchup:
        print("   📊 Auto-catchup enabled: summaries will be generated on each push")
    return True


def uninstall_hook(repo_path: str = ".") -> bool:
    """
    Uninstall pre-push git hook and restore backup if available.
    Also removes old post-commit hook if present.
    
    Args:
        repo_path: Path to git repository
        
    Returns:
        True if uninstallation successful, False otherwise
    """
    # Find git directory
    git_dir = find_git_root(repo_path)
    if not git_dir:
        print("❌ Not a git repository.")
        return False
    
    success = True
    
    # Remove pre-push hook
    hook_path = git_dir / "hooks" / "pre-push"
    backup_path = git_dir / "hooks" / "pre-push.checkpoint-backup"
    
    # Check if our hook is installed
    if not hook_path.exists():
        print("ℹ️  No pre-push checkpoint hook installed.")
        # Check for old post-commit hook
        old_hook = git_dir / "hooks" / "post-commit"
        if old_hook.exists():
            try:
                with open(old_hook, 'r') as f:
                    content = f.read()
                if "Code Checkpoint" in content:
                    old_hook.unlink()
                    print("✅ Removed old post-commit checkpoint hook.")
            except Exception:
                pass
        return True
    
    # Read current hook
    try:
        with open(hook_path, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading hook: {e}")
        return False
    
    # Check if it's our hook
    if "Code Checkpoint" not in content:
        print("⚠️  Hook exists but doesn't appear to be from checkpoint. Skipping removal.")
        return False
    
    # If backup exists, restore it
    if backup_path.exists():
        try:
            shutil.copy2(backup_path, hook_path)
            backup_path.unlink()  # Remove backup
            print("✅ Restored original hook from backup.")
            return True
        except Exception as e:
            print(f"❌ Error restoring backup: {e}")
            return False
    else:
        # No backup, just remove our hook
        try:
            hook_path.unlink()
            print("✅ Removed checkpoint pre-push hook.")
        except Exception as e:
            print(f"❌ Error removing hook: {e}")
            success = False
    
    # Also remove old post-commit hook if it exists
    old_hook = git_dir / "hooks" / "post-commit"
    if old_hook.exists():
        try:
            with open(old_hook, 'r') as f:
                content = f.read()
            if "Code Checkpoint" in content:
                old_hook.unlink()
                print("✅ Removed old post-commit checkpoint hook.")
        except Exception:
            pass
    
    return success


def check_hook_status(repo_path: str = ".") -> dict:
    """
    Check the status of the checkpoint git hook.
    
    Args:
        repo_path: Path to git repository
        
    Returns:
        Dict with status information
    """
    git_dir = find_git_root(repo_path)
    
    if not git_dir:
        return {
            "is_git_repo": False,
            "hook_installed": False,
            "hook_executable": False,
            "backup_exists": False,
            "old_post_commit": False,
        }
    
    hook_path = git_dir / "hooks" / "pre-push"
    backup_path = git_dir / "hooks" / "pre-push.checkpoint-backup"
    old_hook_path = git_dir / "hooks" / "post-commit"
    
    hook_installed = False
    old_post_commit = False
    hook_executable = False
    
    if hook_path.exists():
        try:
            with open(hook_path, 'r') as f:
                content = f.read()
            hook_installed = "Code Checkpoint" in content
            
            # Check if executable
            if os.name != 'nt':  # Unix/Mac
                hook_executable = os.access(hook_path, os.X_OK)
            else:  # Windows
                hook_executable = hook_path.with_suffix('.bat').exists()
        except:
            pass
    
    # Check for old post-commit hook
    if old_hook_path.exists():
        try:
            with open(old_hook_path, 'r') as f:
                content = f.read()
            old_post_commit = "Code Checkpoint" in content
        except:
            pass
    
    return {
        "is_git_repo": True,
        "hook_installed": hook_installed,
        "hook_executable": hook_executable,
        "backup_exists": backup_path.exists(),
        "old_post_commit": old_post_commit,
        "hook_path": str(hook_path) if hook_path.exists() else None,
    }
