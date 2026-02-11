import dspy
import re

def strip_code_fences(text: str) -> str:
    """
    Remove code fence markers (```...``` or longer) from text.
    Handles multiple levels of nesting and various backtick counts.
    Normalizes line endings for cross-platform compatibility.
    """
    if not text:
        return text
    
    # Normalize line endings to \n for consistent regex matching
    text = text.replace('\r\n', '\n').replace('\r', '\n').strip()
    
    # Keep removing outer fence pairs until none are found
    # This handles multiple levels of wrapping (e.g., ```` wrapping ```)
    max_iterations = 10
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        # Try to match any number of backticks (3+) with optional language
        # Pattern: open fence, optional lang, newline, content, newline, close fence
        if text.startswith('```'):
            # Find the closing fence by looking for a line that's just backticks
            lines = text.split('\n')
            
            # Look for a closing fence (line with only backticks)
            close_fence_idx = -1
            for i in range(len(lines) - 1, 0, -1):  # Start from end, skip first line
                line = lines[i].strip()
                if line and all(c == '`' for c in line) and len(line) >= 3:
                    close_fence_idx = i
                    break
            
            if close_fence_idx > 1:
                # Extract content between first and closing fence lines
                content = '\n'.join(lines[1:close_fence_idx])
                text = content.strip()
                # Continue to check for more fences
                continue
        
        break
    
    return text

# === OPTIMIZED: Unified Checkpoint Generation (Single LLM Call) ===

class UnifiedCheckpointSignature(dspy.Signature):
    """
    Unified analysis: Read diff, analyze context, and generate markdown in a single LLM call.
    Reduces API latency by 66% (one round-trip instead of three).
    """
    diff_content = dspy.InputField(desc="The raw text of the git diff.")
    
    # All outputs together
    summary = dspy.OutputField(desc="A high-level summary of the file changes.")
    technical_details = dspy.OutputField(desc="List of specific functions, classes, or logic modified.")
    intent = dspy.OutputField(desc="The deduced intent behind the changes (Why was this done?).")
    architectural_impact = dspy.OutputField(desc="Explanation of how this affects the broader architecture or specific modules.")
    markdown_content = dspy.OutputField(desc="The formatted markdown content for the checkpoint, including headers for Context, Changes, and Impact.")

class CheckpointGenerator(dspy.Module):
    """
    Optimized checkpoint generator using a single unified LLM call.
    """
    def __init__(self):
        super().__init__()
        self.unified = dspy.ChainOfThought(UnifiedCheckpointSignature)

    def forward(self, diff_content):
        # Single LLM call generates all outputs
        result = self.unified(diff_content=diff_content)
        # Strip code fences from markdown output
        result.markdown_content = strip_code_fences(result.markdown_content)
        return result

# === LEGACY: Three-Stage Pipeline (Deprecated but kept for reference) ===

class DiffReader(dspy.Signature):
    """
    Analyzes a git diff to understand what files were changed and the nature of the changes.
    """
    diff_content = dspy.InputField(desc="The raw text of the git diff.")
    summary = dspy.OutputField(desc="A high-level summary of the file changes.")
    technical_details = dspy.OutputField(desc="List of specific functions, classes, or logic modified.")

class ContextAnalyzer(dspy.Signature):
    """
    Determines the intent and architectural impact of the changes based on the diff analysis.
    """
    summary = dspy.InputField(desc="Summary of file changes.")
    technical_details = dspy.InputField(desc="Technical details of changes.")
    intent = dspy.OutputField(desc="The deduced intent behind the changes (Why was this done?).")
    architectural_impact = dspy.OutputField(desc="Explanation of how this affects the broader architecture or specific modules.")

class MarkdownWriter(dspy.Signature):
    """
    Generates a structured markdown checkpoint based on the analysis.
    """
    intent = dspy.InputField(desc="The intent behind changes.")
    architectural_impact = dspy.InputField(desc="The architectural impact.")
    technical_details = dspy.InputField(desc="Technical details of changes.")
    markdown_content = dspy.OutputField(desc="The formatted markdown content for the checkpoint, including headers for Context, Changes, and Impact.")

class LegacyCheckpointGenerator(dspy.Module):
    """
    DEPRECATED: Original three-stage pipeline (kept for backward compatibility).
    Use CheckpointGenerator instead for 66% faster execution.
    """
    def __init__(self):
        super().__init__()
        self.diff_reader = dspy.ChainOfThought(DiffReader)
        self.context_analyzer = dspy.ChainOfThought(ContextAnalyzer)
        self.markdown_writer = dspy.ChainOfThought(MarkdownWriter)

    def forward(self, diff_content):
        # Step 1: Read Diff
        diff_analysis = self.diff_reader(diff_content=diff_content)
        
        # Step 2: Analyze Context
        context_analysis = self.context_analyzer(
            summary=diff_analysis.summary,
            technical_details=diff_analysis.technical_details
        )
        
        # Step 3: Write Markdown
        markdown_output = self.markdown_writer(
            intent=context_analysis.intent,
            architectural_impact=context_analysis.architectural_impact,
            technical_details=diff_analysis.technical_details
        )
        
        return markdown_output

# === Advanced Workflows: Catchup & Onboarding ===

class CatchupSummarizer(dspy.Signature):
    """
    Synthesizes multiple past checkpoints into a single personalized summary for a returning developer.
    Focuses on "While You Were Gone" changes, new dependencies, and refactors.
    """
    checkpoints_content = dspy.InputField(desc="The content of multiple markdown checkpoints created since the user's last work.")
    user_last_active_date = dspy.InputField(desc="The date the user was last active.")
    
    summary_markdown = dspy.OutputField(desc="A concise markdown summary titled 'While You Were Gone'. Sections: Changes Summary, New Dependencies, Refactors, Current Focus.")

class CatchupGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.summarizer = dspy.ChainOfThought(CatchupSummarizer)
    
    def forward(self, checkpoints_content, user_last_active_date):
        result = self.summarizer(
            checkpoints_content=checkpoints_content,
            user_last_active_date=user_last_active_date
        )
        # Strip code fences from markdown output
        result.summary_markdown = strip_code_fences(result.summary_markdown)
        return result

class OnboardingSynthesizer(dspy.Signature):
    """
    Generates a 'Master Context' document for a new developer (The Map).
    Explains architecture, key decisions, gotchas, and dependencies basically telling the 'Story' of the codebase.
    """
    file_structure = dspy.InputField(desc="The file tree structure of the repository.")
    recent_checkpoints = dspy.InputField(desc="Recent high-level checkpoints to understand history.")
    dependency_graph = dspy.InputField(desc="Mermaid.js diagram showing file dependencies.")
    class_hierarchy = dspy.InputField(desc="Mermaid.js diagram showing class inheritance.")
    
    master_markdown = dspy.OutputField(desc="A comprehensive guide. Sections: Architectural Overview, Key Decision Log, Gotchas & Tech Debt, Dependency Map (Include the provided mermaid diagrams here).")

class MasterContextGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.synthesizer = dspy.ChainOfThought(OnboardingSynthesizer)
        
    def forward(self, file_structure, recent_checkpoints, dependency_graph, class_hierarchy):
        result = self.synthesizer(
            file_structure=file_structure,
            recent_checkpoints=recent_checkpoints,
            dependency_graph=dependency_graph,
            class_hierarchy=class_hierarchy
        )
        # Strip code fences if the LLM wrapped output in markdown code blocks
        result.master_markdown = strip_code_fences(result.master_markdown)
        return result
