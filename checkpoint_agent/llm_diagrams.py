"""LLM-based diagram generation for language-agnostic architecture visualization."""
from pathlib import Path
from typing import Tuple


def get_sample_files(repo_path: str = ".", max_files: int = 10, max_lines_per_file: int = 100) -> str:
    """
    Extract sample code files from repository for LLM analysis.

    Args:
        repo_path: Path to repository
        max_files: Maximum number of files to sample
        max_lines_per_file: Maximum lines per file to include

    Returns:
        String containing concatenated file contents with headers
    """
    path = Path(repo_path)

    priority_patterns = [
        "main.py", "app.py", "index.js", "index.ts", "main.go", "main.rs",
        "server.py", "server.js", "app.js", "app.ts",
        "README.md", "setup.py", "package.json", "go.mod", "Cargo.toml",
        "__init__.py", "config.py", "settings.py"
    ]

    ignore_dirs = {'.git', 'node_modules', 'venv', '__pycache__', 'build', 'dist', '.pytest_cache', 'target'}
    ignore_extensions = {'.pyc', '.pyo', '.so', '.dylib', '.dll', '.exe', '.png', '.jpg', '.jpeg', '.gif', '.svg'}

    sampled_files = []

    for pattern in priority_patterns:
        for file_path in path.rglob(pattern):
            if any(ignored in file_path.parts for ignored in ignore_dirs):
                continue
            if file_path.suffix in ignore_extensions:
                continue
            if file_path.is_file():
                sampled_files.append(file_path)
                if len(sampled_files) >= max_files:
                    break
        if len(sampled_files) >= max_files:
            break

    if len(sampled_files) < max_files:
        for pattern in ["src/**/*", "lib/**/*", "app/**/*"]:
            for file_path in path.glob(pattern):
                if any(ignored in file_path.parts for ignored in ignore_dirs):
                    continue
                if file_path.suffix in ignore_extensions:
                    continue
                if file_path.is_file() and file_path not in sampled_files:
                    sampled_files.append(file_path)
                    if len(sampled_files) >= max_files:
                        break
            if len(sampled_files) >= max_files:
                break

    content_parts = []
    for file_path in sampled_files[:max_files]:
        try:
            relative_path = file_path.relative_to(path)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                if len(lines) > max_lines_per_file:
                    lines = lines[:max_lines_per_file] + [f"\n... ({len(lines) - max_lines_per_file} more lines) ...\n"]
                content = ''.join(lines)
            content_parts.append(f"### File: {relative_path}\n```\n{content}\n```\n")
        except Exception:
            continue

    return "\n\n".join(content_parts)


def generate_diagrams_llm(repo_path: str = ".", languages: list = None) -> Tuple[str, str]:
    """
    Generate Mermaid diagrams using direct LLM analysis (language-agnostic).

    Args:
        repo_path: Path to repository
        languages: List of detected languages (optional)

    Returns:
        Tuple of (dependency_graph, architecture_diagram) as Mermaid strings
    """
    import subprocess
    from checkpoint_agent.agents import _call_llm, strip_code_fences

    try:
        result = subprocess.run(
            ["tree", "-L", "3", "-I", "__pycache__|venv|.git|node_modules"],
            capture_output=True, text=True, cwd=repo_path
        )
        file_structure = result.stdout if result.returncode == 0 else ""
        if not file_structure:
            result = subprocess.run(
                ["find", ".", "-maxdepth", "3", "-not", "-path", "*/.*"],
                capture_output=True, text=True, cwd=repo_path
            )
            file_structure = result.stdout
    except Exception:
        file_structure = "File structure unavailable"

    sample_files = get_sample_files(repo_path)
    languages_str = ", ".join(languages) if languages else "Unknown"

    system_prompt = (
        "You are an expert software architect. Generate concise Mermaid.js diagrams "
        "from repository structure and code samples. Return only valid Mermaid syntax, no explanations."
    )

    dep_prompt = (
        f"Repository languages: {languages_str}\n\n"
        f"File structure:\n{file_structure}\n\n"
        f"Sample files:\n{sample_files}\n\n"
        "Generate a Mermaid.js flowchart (graph TD) showing file/module dependencies. "
        "Use --> for dependencies. Include main entry points and key modules only. "
        "Return only the Mermaid diagram syntax."
    )

    arch_prompt = (
        f"Repository languages: {languages_str}\n\n"
        f"File structure:\n{file_structure}\n\n"
        f"Sample files:\n{sample_files}\n\n"
        "Generate a Mermaid.js diagram showing the high-level system architecture "
        "(components, layers, data flow). Use graph TD or C4 diagram style. "
        "Return only the Mermaid diagram syntax."
    )

    try:
        dependency_graph = strip_code_fences(_call_llm(system_prompt, dep_prompt))
    except Exception as e:
        dependency_graph = f"graph TD\n    A[Error generating diagram: {e}]"

    try:
        architecture_diagram = strip_code_fences(_call_llm(system_prompt, arch_prompt))
    except Exception as e:
        architecture_diagram = f"graph TD\n    A[Error generating diagram: {e}]"

    return dependency_graph, architecture_diagram


def should_use_llm_diagrams(config) -> bool:
    """
    Determine if LLM-based diagram generation should be used.

    Returns True for multi-language or non-Python repos, False for Python-only.
    """
    if not config.features.diagrams:
        return False

    if len(config.languages) == 1 and config.languages[0].lower() == "python":
        return False

    return True
