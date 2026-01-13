import os
import ast
from pathlib import Path

def get_python_files(root_path: str):
    """Yields all python files in the directory."""
    for root, _, files in os.walk(root_path):
        if "venv" in root or ".git" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                yield os.path.join(root, file)

def generate_file_dependency_mermaid(root_path: str) -> str:
    """
    Scans the codebase for imports and generates a Mermaid graph TD.
    """
    dependencies = set()
    
    # Map from file name (not full path) to full path for resolution
    # This is a simplification; in a real project you'd resolve python paths properly.
    # For this task, we'll assume unique filenames or best-effort matching.
    file_map = {}
    for file_path in get_python_files(root_path):
        filename = os.path.basename(file_path).replace(".py", "")
        file_map[filename] = file_path

    for file_path in get_python_files(root_path):
        source_node = os.path.basename(file_path).replace(".py", "")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except Exception:
            # Skip files that can't be parsed
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # simplistic: if we import 'src.agents', we link to 'agents'
                    target = alias.name.split('.')[-1]
                    if target in file_map and target != source_node:
                        dependencies.add((source_node, target))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    target = node.module.split('.')[-1]
                    if target in file_map and target != source_node:
                         dependencies.add((source_node, target))

    if not dependencies:
        return ""

    mermaid = "```mermaid\ngraph TD\n"
    for src, dst in sorted(dependencies):
        mermaid += f"    {src} --> {dst}\n"
    mermaid += "```"
    
    return mermaid

def generate_class_hierarchy_mermaid(root_path: str) -> str:
    """
    Scans for class definitions and their base classes to build a class diagram.
    """
    inheritance = set()
    
    # Track all classes defined in the repo to filter external bases if desired
    # For now, we'll include everything to see what it looks like
    defined_classes = set()

    for file_path in get_python_files(root_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                defined_classes.add(node.name)
                for base in node.bases:
                    # Handle simplistic base names
                    if isinstance(base, ast.Name):
                        inheritance.add((base.id, node.name))
                    elif isinstance(base, ast.Attribute):
                         inheritance.add((base.attr, node.name))
    
    if not inheritance:
        return ""

    mermaid = "```mermaid\nclassDiagram\n"
    for base, derived in sorted(inheritance):
        mermaid += f"    {base} <|-- {derived}\n"
    mermaid += "```"
    
    return mermaid
