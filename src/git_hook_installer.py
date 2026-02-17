"""Git hook installation and management."""
import os
import shutil
import stat
from pathlib import Path
from typing import Optional


def get_hook_template(auto_catchup: bool = False) -> str:
    """
    Generate hook template based on configuration.
    
    Args:
        auto_catchup: Whether to auto-generate catchup summaries
        
    Returns:
        Hook script content
    """
    base_hook = """#!/bin/sh
# Code Checkpoint Auto-generated Hook
# This hook generates checkpoints automatically after each commit

# Get the commit hash
COMMIT_HASH=$(git rev-parse HEAD)

# Run checkpoint in background to avoid blocking commit
# Redirect output to log file
checkpoint --commit "$COMMIT_HASH" >> .checkpoint.log 2>&1 &
"""
    
    if auto_catchup:
        base_hook += """
# Auto-generate catchup summaries for all active developers
checkpoint --catchup-all >> .checkpoint.log 2>&1 &
"""
    
    return base_hook


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
    Install post-commit git hook for automatic checkpoint generation.
    
    Uses a composition pattern: if an existing hook is found, it's backed up
    and the checkpoint command is appended to preserve existing functionality.
    
    Args:
        repo_path: Path to git repository
        force: If True, overwrite existing checkpoint hook
        auto_catchup: If True, include auto-catchup in hook
        
    Returns:
        True if installation successful, False otherwise
    """
    # Generate hook template based on config
    hook_template = get_hook_template(auto_catchup)
    
    # Find git directory
    git_dir = find_git_root(repo_path)
    if not git_dir:
        print("❌ Not a git repository. Run 'git init' first.")
        return False
    
    hooks_dir = git_dir / "hooks"
    hook_path = hooks_dir / "post-commit"
    
    # Ensure hooks directory exists
    hooks_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if existing hook exists
    exists, existing_content = check_existing_hook(git_dir, "post-commit")
    
    if exists and existing_content:
        # Check if it's already our hook
        if "Code Checkpoint Auto-generated Hook" in existing_content:
            if not force:
                print("✅ Checkpoint hook already installed.")
                return True
            else:
                print("♻️  Reinstalling checkpoint hook...")
        
        # Check if it's a user hook (not ours)
        if "Code Checkpoint" not in existing_content:
            print(f"⚠️  Existing {hook_path.name} hook detected.")
            
            # Backup the existing hook
            if not backup_existing_hook(git_dir, "post-commit"):
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
            print("✅ Installed checkpoint post-commit hook.")
        except Exception as e:
            print(f"❌ Error creating hook: {e}")
            return False
    
    # Make executable
    if not make_executable(hook_path):
        return False
    
    print(f"✅ Hook installed at {hook_path}")
    print("   Checkpoints will be generated automatically after each commit.")
    return True


def uninstall_hook(repo_path: str = ".") -> bool:
    """
    Uninstall post-commit git hook and restore backup if available.
    
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
    
    hook_path = git_dir / "hooks" / "post-commit"
    backup_path = git_dir / "hooks" / "post-commit.checkpoint-backup"
    
    # Check if our hook is installed
    if not hook_path.exists():
        print("✅ No checkpoint hook installed.")
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
            print("✅ Removed checkpoint hook.")
            return True
        except Exception as e:
            print(f"❌ Error removing hook: {e}")
            return False


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
        }
    
    hook_path = git_dir / "hooks" / "post-commit"
    backup_path = git_dir / "hooks" / "post-commit.checkpoint-backup"
    
    hook_installed = False
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
    
    return {
        "is_git_repo": True,
        "hook_installed": hook_installed,
        "hook_executable": hook_executable,
        "backup_exists": backup_path.exists(),
        "hook_path": str(hook_path) if hook_path.exists() else None,
    }
