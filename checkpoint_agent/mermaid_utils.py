import os
import ast
from pathlib import Path
from functools import lru_cache
from typing import Tuple

# Mermaid reserved keywords that cannot be used as node IDs
MERMAID_RESERVED_KEYWORDS = {
    'graph', 'flowchart', 'subgraph', 'end', 'direction',
    'tb', 'bt', 'rl', 'lr', 'td',
    'node', 'link', 'click', 'classDef', 'class', 'style',
    'linkStyle', 'acc_title', 'acc_descr',
    'true', 'false', 'and', 'or', 'not', 'xor'
}

def sanitize_node_id(node_id: str) -> str:
    """
    Sanitize node ID to avoid Mermaid reserved keywords.
    If the ID is a reserved keyword, prefix it with 'mod_'.
    """
    if node_id.lower() in MERMAID_RESERVED_KEYWORDS:
        return f"mod_{node_id}"
    # Also sanitize special characters
    sanitized = "".join(c if c.isalnum() or c == '_' else '_' for c in node_id)
    return sanitized if sanitized else "node"

def get_python_files(root_path: str):
    """Yields all python files in the directory."""
    for root, _, files in os.walk(root_path):
        if "venv" in root or ".git" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                yield os.path.join(root, file)

@lru_cache(maxsize=512)
def _parse_file_cached(file_path: str, mtime: float) -> Tuple[set, set, str]:
    """
    Parse a Python file once and extract both imports and class definitions.
    Cached by file path and modification time for performance.
    Returns: (dependencies, inheritance_relations, source_node)
    """
    dependencies = set()
    inheritance = set()
    source_node = os.path.basename(file_path).replace(".py", "")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except Exception:
        return dependencies, inheritance, source_node

    for node in ast.walk(tree):
        # Extract imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                target = alias.name.split('.')[-1]
                if target != source_node:
                    dependencies.add((source_node, target))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                target = node.module.split('.')[-1]
                if target != source_node:
                    dependencies.add((source_node, target))
        
        # Extract class hierarchies
        elif isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name):
                    inheritance.add((base.id, node.name))
                elif isinstance(base, ast.Attribute):
                    inheritance.add((base.attr, node.name))
    
    return dependencies, inheritance, source_node

def generate_all_mermaid_diagrams(root_path: str, depth_limit: int = None) -> Tuple[str, str]:
    """
    Single-pass analysis: Parse each Python file once and generate both diagrams.
    Node IDs are sanitized to avoid Mermaid reserved keywords.
    Args:
        root_path: Root directory to scan
        depth_limit: Optional limit for dependency graph depth (reduces context size)
    Returns:
        (dependency_graph_mermaid, class_hierarchy_mermaid)
    """
    all_dependencies = set()
    all_inheritance = set()
    file_map = {}
    
    # Single pass: parse each file once
    for file_path in get_python_files(root_path):
        filename = os.path.basename(file_path).replace(".py", "")
        file_map[filename] = file_path
        
        # Get file modification time for cache key
        try:
            mtime = os.path.getmtime(file_path)
        except:
            mtime = 0
        
        deps, inheritance, _ = _parse_file_cached(file_path, mtime)
        all_dependencies.update(deps)
        all_inheritance.update(inheritance)
    
    # Filter dependencies to only include files in our codebase and sanitize node IDs
    filtered_deps = set()
    for src, dst in all_dependencies:
        if dst in file_map:
            sanitized_src = sanitize_node_id(src)
            sanitized_dst = sanitize_node_id(dst)
            filtered_deps.add((sanitized_src, sanitized_dst))
    
    # Apply depth limit if specified (for large repos, limit to top-level modules)
    if depth_limit:
        # Simple depth limiting: only include dependencies with short paths
        filtered_deps = {(src, dst) for src, dst in filtered_deps if len(src.split('.')) <= depth_limit}
    
    # Generate dependency graph with sanitized node IDs
    dep_mermaid = ""
    if filtered_deps:
        dep_mermaid = "```mermaid\ngraph TD\n"
        for src, dst in sorted(filtered_deps):
            dep_mermaid += f"    {src} --> {dst}\n"
        dep_mermaid += "```"
    
    # Generate class hierarchy with sanitized node IDs
    class_mermaid = ""
    if all_inheritance:
        class_mermaid = "```mermaid\nclassDiagram\n"
        sanitized_inheritance = set()
        for base, derived in all_inheritance:
            sanitized_base = sanitize_node_id(base)
            sanitized_derived = sanitize_node_id(derived)
            sanitized_inheritance.add((sanitized_base, sanitized_derived))
        
        for base, derived in sorted(sanitized_inheritance):
            class_mermaid += f"    {base} <|-- {derived}\n"
        class_mermaid += "```"
    
    return dep_mermaid, class_mermaid

