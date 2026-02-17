"""LLM-based diagram generation for language-agnostic architecture visualization."""
import dspy
from pathlib import Path
from typing import Tuple


class DiagramGeneratorSignature(dspy.Signature):
    """
    Generate Mermaid.js diagrams from repository structure and code samples.
    Works for any programming language via semantic understanding.
    """
    file_structure = dspy.InputField(desc="Complete file tree structure of the repository")
    sample_files = dspy.InputField(desc="Contents of 5-10 key code files")
    languages = dspy.InputField(desc="Detected programming languages in the repository")
    
    dependency_graph = dspy.OutputField(desc="Mermaid.js flowchart showing file/module dependencies. Use --> for dependencies. Include main entry points and key modules.")
    architecture_diagram = dspy.OutputField(desc="Mermaid.js diagram showing high-level system architecture (components, layers, data flow). Use graph TD or C4 diagram style.")


class LLMDiagramGenerator(dspy.Module):
    """
    Generate architecture diagrams using LLM semantic understanding.
    Language-agnostic alternative to AST-based parsing.
    """
    def __init__(self):
        super().__init__()
        self.generator = dspy.ChainOfThought(DiagramGeneratorSignature)
    
    def forward(self, file_structure: str, sample_files: str, languages: str):
        result = self.generator(
            file_structure=file_structure,
            sample_files=sample_files,
            languages=languages
        )
        return result


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
    
    # Priority file patterns (look for these first)
    priority_patterns = [
        "main.py", "app.py", "index.js", "index.ts", "main.go", "main.rs",
        "server.py", "server.js", "app.js", "app.ts",
        "README.md", "setup.py", "package.json", "go.mod", "Cargo.toml",
        "__init__.py", "config.py", "settings.py"
    ]
    
    # Common ignore patterns
    ignore_dirs = {'.git', 'node_modules', 'venv', '__pycache__', 'build', 'dist', '.pytest_cache', 'target'}
    ignore_extensions = {'.pyc', '.pyo', '.so', '.dylib', '.dll', '.exe', '.png', '.jpg', '.jpeg', '.gif', '.svg'}
    
    sampled_files = []
    
    # First, try to get priority files
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
    
    # If we need more files, sample from src/ or lib/ directories
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
    
    # Build concatenated content
    content_parts = []
    for file_path in sampled_files[:max_files]:
        try:
            relative_path = file_path.relative_to(path)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                # Truncate if too long
                if len(lines) > max_lines_per_file:
                    lines = lines[:max_lines_per_file] + [f"\n... ({len(lines) - max_lines_per_file} more lines) ...\n"]
                content = ''.join(lines)
            
            content_parts.append(f"### File: {relative_path}\n```\n{content}\n```\n")
        except Exception as e:
            # Skip files that can't be read
            continue
    
    return "\n\n".join(content_parts)


def generate_diagrams_llm(repo_path: str = ".", languages: list[str] = None) -> Tuple[str, str]:
    """
    Generate Mermaid diagrams using LLM analysis (language-agnostic).
    
    Args:
        repo_path: Path to repository
        languages: List of detected languages (optional)
        
    Returns:
        Tuple of (dependency_graph, architecture_diagram) as Mermaid strings
    """
    import subprocess
    
    # Get file structure
    try:
        result = subprocess.run(
            ["tree", "-L", "3", "-I", "__pycache__|venv|.git|node_modules"],
            capture_output=True,
            text=True,
            cwd=repo_path
        )
        if result.returncode == 0:
            file_structure = result.stdout
        else:
            # Fallback to find
            result = subprocess.run(
                ["find", ".", "-maxdepth", "3", "-not", "-path", "*/.*"],
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            file_structure = result.stdout
    except Exception:
        file_structure = "File structure unavailable"
    
    # Get sample files
    sample_files = get_sample_files(repo_path)
    
    # Format languages
    languages_str = ", ".join(languages) if languages else "Unknown"
    
    # Generate diagrams using LLM
    generator = LLMDiagramGenerator()
    result = generator(
        file_structure=file_structure,
        sample_files=sample_files,
        languages=languages_str
    )
    
    # Clean diagram output (remove any extra markdown fences)
    from src.agents import strip_code_fences
    dependency_graph = strip_code_fences(result.dependency_graph)
    architecture_diagram = strip_code_fences(result.architecture_diagram)
    
    return dependency_graph, architecture_diagram


def should_use_llm_diagrams(config) -> bool:
    """
    Determine if LLM-based diagram generation should be used.
    
    Args:
        config: CheckpointConfig instance
        
    Returns:
        True if LLM diagrams should be used, False otherwise
    """
    # Use LLM diagrams if:
    # 1. Diagrams are enabled in config
    # 2. Multiple languages detected or non-Python primary language
    
    if not config.features.diagrams:
        return False
    
    # If Python is the only or primary language, can use AST
    # Otherwise, use LLM for universality
    if len(config.languages) == 1 and config.languages[0].lower() == "python":
        return False  # Use faster AST approach
    
    return True  # Use LLM for multi-language or non-Python
