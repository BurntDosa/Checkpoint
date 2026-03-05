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
    You are a senior software engineer documenting a code change for your team.
    Analyze the provided git diff and produce a thorough, structured checkpoint document.
    Write for a developer returning after time away — they need full context, not just a summary.
    Use specific file names, function names, and module names throughout.
    """
    diff_content = dspy.InputField(desc="The raw text of the git diff.")

    summary = dspy.OutputField(
        desc="2-4 sentences giving a high-level overview of what changed. "
             "Mention affected components, files, and modules by name. "
             "Avoid vague language like 'various changes' — be specific."
    )
    technical_details = dspy.OutputField(
        desc="Detailed bullet-point list of every specific change. "
             "Group by file. Include function names, class names, and argument changes. "
             "Example: '- src/agents.py: Added `PRSummarySignature` class with inputs pr_title, pr_number, combined_diff'"
    )
    intent = dspy.OutputField(
        desc="2-3 sentences explaining WHY these changes were made. "
             "Distinguish between: bug fix (what was broken), feature addition (what capability is new), "
             "refactor (what was improved without behavior change), or dependency update (why upgraded)."
    )
    architectural_impact = dspy.OutputField(
        desc="Address all four of: "
             "(1) Which modules/layers are affected and how they interact differently now. "
             "(2) Data flow changes — does data move through different paths or in different shapes. "
             "(3) Ripple effects — what other parts of the codebase will need to adapt. "
             "(4) Breaking changes — any API, schema, or interface changes that require callers to update."
    )
    markdown_content = dspy.OutputField(
        desc="The complete formatted checkpoint document in markdown. "
             "MUST include exactly these sections in order: "
             "## Context (background on why this change exists), "
             "## Changes (grouped by file with specific function/class names), "
             "## Impact (architectural and downstream effects), "
             "## Priority Rating (one of: CRITICAL / HIGH / MEDIUM / LOW with one sentence justification). "
             "Target length: 400-800 words. Be specific and concrete throughout."
    )

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
    You are writing a personalized 'While You Were Gone' briefing for a developer returning to the codebase.
    Your goal is to get them fully up to speed in one read — covering what changed, what's new, what broke,
    and what they need to act on immediately. Be direct, specific, and prioritize ruthlessly.
    Name specific files, functions, modules, and authors where relevant.
    Target length: 500-1000 words.
    """
    checkpoints_content = dspy.InputField(desc="The content of multiple markdown checkpoints created since the user's last work.")
    user_last_active_date = dspy.InputField(desc="The date the user was last active.")

    summary_markdown = dspy.OutputField(
        desc="A comprehensive markdown briefing. "
             "MUST include exactly these sections in order: "
             "# While You Were Gone — Since {user_last_active_date} "
             "(include the actual date from user_last_active_date in the heading, e.g. '# While You Were Gone — Since 2026-02-11'. "
             "2-3 sentence executive summary of the period), "
             "## Critical Changes (Must-Read) (breaking changes, API changes, anything that will block their work immediately), "
             "## New Features & Additions (new capabilities, endpoints, modules added), "
             "## Refactors & Structural Changes (reorganizations, renames, performance improvements), "
             "## New Dependencies & Config Changes (new packages, env vars, config keys added or changed), "
             "## Current Focus Areas (what the team is actively working on, what PRs/features are in flight). "
             "Target length: 500-1000 words."
    )

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
    You are writing the definitive onboarding document for a new engineer joining this codebase.
    This is 'The Map' — it should tell the story of the codebase: why it exists, how it's structured,
    what decisions were made and why, where the bodies are buried (gotchas, tech debt), and how to get started.
    A new engineer should be able to read this and understand the full system without reading the code first.
    Target length: 1500+ words.
    """
    file_structure = dspy.InputField(desc="The file tree structure of the repository.")
    recent_checkpoints = dspy.InputField(desc="Recent high-level checkpoints to understand history.")
    dependency_graph = dspy.InputField(desc="Mermaid.js diagram showing file dependencies.")
    class_hierarchy = dspy.InputField(desc="Mermaid.js diagram showing class inheritance.")

    master_markdown = dspy.OutputField(
        desc="A comprehensive onboarding guide in markdown. "
             "MUST include exactly these sections in order: "
             "# Master Context (one-paragraph mission statement for the codebase), "
             "## Architecture Overview (how the system is structured, key data flows, component interactions — include the provided Mermaid diagrams here), "
             "## Key Decision Log (3-5 important architectural or technical decisions made, with rationale), "
             "## Gotchas & Tech Debt (non-obvious things that will trip up new engineers, known issues, temporary hacks), "
             "## Dependency Map (external services, APIs, and libraries the system depends on, with their roles), "
             "## Getting Started (step-by-step guide to set up the environment and make a first contribution). "
             "Target length: 1500+ words. Be specific — name actual files, classes, and functions."
    )

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

# === PR Support ===

class PRSummarySignature(dspy.Signature):
    """
    You are a senior engineer writing a pull request summary for reviewers and for future reference.
    This document should give reviewers everything they need to understand the PR's purpose, scope, and risk
    without reading every line of code. It also serves as a historical record of what changed and why.
    Target length: 600-1200 words.
    """
    pr_title = dspy.InputField(desc="The title of the pull request.")
    pr_number = dspy.InputField(desc="The pull request number.")
    base_branch = dspy.InputField(desc="The base branch being merged into (e.g., main).")
    head_branch = dspy.InputField(desc="The feature branch being merged (e.g., feature/auth).")
    combined_diff = dspy.InputField(desc="The combined git diff for all changes in this PR.")
    commit_checkpoints = dspy.InputField(desc="Individual checkpoint summaries for each commit in the PR.")

    pr_summary_markdown = dspy.OutputField(
        desc="A complete PR summary document in markdown. "
             "MUST include exactly these sections in order: "
             "## Overview (2-3 sentences: what this PR does and why it exists), "
             "## Changes by Area (changes grouped by module/concern, with specific file and function names), "
             "## Commit Walkthrough (brief summary of each commit's purpose in chronological order), "
             "## Architectural Impact (what changes in the system design, data flow, or interfaces), "
             "## Review Notes (specific areas reviewers should focus on, potential risks, edge cases to test), "
             "## Priority Rating (one of: CRITICAL / HIGH / MEDIUM / LOW with justification). "
             "Target length: 600-1200 words."
    )

class PRSummaryGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.summarizer = dspy.ChainOfThought(PRSummarySignature)

    def forward(self, pr_title, pr_number, base_branch, head_branch, combined_diff, commit_checkpoints):
        result = self.summarizer(
            pr_title=pr_title,
            pr_number=str(pr_number),
            base_branch=base_branch,
            head_branch=head_branch,
            combined_diff=combined_diff,
            commit_checkpoints=commit_checkpoints
        )
        result.pr_summary_markdown = strip_code_fences(result.pr_summary_markdown)
        return result
