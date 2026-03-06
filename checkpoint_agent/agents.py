import re
import litellm
from types import SimpleNamespace


def strip_code_fences(text: str) -> str:
    """
    Remove code fence markers (```...``` or longer) from text.
    Handles multiple levels of nesting and various backtick counts.
    Normalizes line endings for cross-platform compatibility.
    """
    if not text:
        return text

    text = text.replace('\r\n', '\n').replace('\r', '\n').strip()

    max_iterations = 10
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        if text.startswith('```'):
            lines = text.split('\n')
            close_fence_idx = -1
            for i in range(len(lines) - 1, 0, -1):
                line = lines[i].strip()
                if line and all(c == '`' for c in line) and len(line) >= 3:
                    close_fence_idx = i
                    break
            if close_fence_idx > 1:
                content = '\n'.join(lines[1:close_fence_idx])
                text = content.strip()
                continue
        break

    return text


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """Make a single LiteLLM completion call using the current config."""
    from checkpoint_agent.llm import _llm_config
    config = _llm_config
    response = litellm.completion(
        model=config["model"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
    )
    return response.choices[0].message.content or ""


class CheckpointGenerator:
    """
    Generates a structured checkpoint document from a git diff.
    Replaces DSPy UnifiedCheckpointSignature + CheckpointGenerator.
    """
    def __call__(self, diff_content: str) -> SimpleNamespace:
        system = (
            "You are a senior software engineer documenting a code change for your team. "
            "Analyze the provided git diff and produce a thorough, structured checkpoint document. "
            "Write for a developer returning after time away — they need full context, not just a summary. "
            "Use specific file names, function names, and module names throughout."
        )
        user = (
            "Analyze this git diff and produce a checkpoint document.\n\n"
            "MUST include exactly these sections in order:\n"
            "## Context (background on why this change exists)\n"
            "## Changes (grouped by file with specific function/class names)\n"
            "## Impact (architectural and downstream effects)\n"
            "## Priority Rating (one of: CRITICAL / HIGH / MEDIUM / LOW with one sentence justification)\n\n"
            "Target length: 400-800 words. Be specific and concrete throughout.\n\n"
            f"Git diff:\n{diff_content}"
        )
        content = strip_code_fences(_call_llm(system, user))
        return SimpleNamespace(markdown_content=content)


class CatchupGenerator:
    """
    Generates or updates a 'While You Were Gone' briefing for a returning developer.
    Replaces DSPy CatchupSummarizer + CatchupGenerator.
    """
    def __call__(self, checkpoints_content: str, user_last_active_date: str,
                 existing_catchup: str = None) -> SimpleNamespace:
        if existing_catchup:
            system = (
                "You are maintaining a 'While You Were Gone' briefing for a developer. "
                "An existing catchup document exists — update it to incorporate new changes. "
                "Preserve ALL information from the existing document. Add new information under the "
                "appropriate sections or append new sections for major new changes. "
                "Do not remove or contradict existing information. "
                "Name specific files, functions, modules, and authors where relevant."
            )
            user = (
                f"Update this catchup document with new checkpoints.\n\n"
                "Rules:\n"
                "- Keep ALL existing content intact\n"
                "- Add new information from the checkpoints below into the appropriate sections\n"
                "- If a section already covers a topic, extend it rather than duplicate it\n"
                "- Update the executive summary to reflect the full period\n\n"
                f"Existing catchup document:\n{existing_catchup}\n\n"
                f"New checkpoints to incorporate:\n{checkpoints_content}"
            )
        else:
            system = (
                "You are writing a personalized 'While You Were Gone' briefing for a developer returning to the codebase. "
                "Your goal is to get them fully up to speed in one read — covering what changed, what's new, what broke, "
                "and what they need to act on immediately. Be direct, specific, and prioritize ruthlessly. "
                "Name specific files, functions, modules, and authors where relevant. "
                "Target length: 500-1000 words."
            )
            user = (
                f"Write a catchup briefing for a developer who was last active on {user_last_active_date}.\n\n"
                "MUST include exactly these sections in order:\n"
                f"# While You Were Gone — Since {user_last_active_date}\n"
                "(2-3 sentence executive summary of the period)\n"
                "## Critical Changes (Must-Read) (breaking changes, API changes, anything that will block their work immediately)\n"
                "## New Features & Additions (new capabilities, endpoints, modules added)\n"
                "## Refactors & Structural Changes (reorganizations, renames, performance improvements)\n"
                "## New Dependencies & Config Changes (new packages, env vars, config keys added or changed)\n"
                "## Current Focus Areas (what the team is actively working on, what PRs/features are in flight)\n\n"
                "Target length: 500-1000 words.\n\n"
                f"Checkpoints to summarize:\n{checkpoints_content}"
            )
        content = strip_code_fences(_call_llm(system, user))
        return SimpleNamespace(summary_markdown=content)


class MasterContextGenerator:
    """
    Generates the definitive onboarding document for a new engineer.
    Replaces DSPy OnboardingSynthesizer + MasterContextGenerator.
    """
    def __call__(self, file_structure: str, recent_checkpoints: str,
                 dependency_graph: str, class_hierarchy: str) -> SimpleNamespace:
        system = (
            "You are writing the definitive onboarding document for a new engineer joining this codebase. "
            "This is 'The Map' — it should tell the story of the codebase: why it exists, how it's structured, "
            "what decisions were made and why, where the bodies are buried (gotchas, tech debt), and how to get started. "
            "A new engineer should be able to read this and understand the full system without reading the code first. "
            "Target length: 1500+ words."
        )
        user = (
            "Generate a master onboarding document for this codebase.\n\n"
            "MUST include exactly these sections in order:\n"
            "# Master Context (one-paragraph mission statement for the codebase)\n"
            "## Architecture Overview (how the system is structured, key data flows, component interactions — include the provided Mermaid diagrams here)\n"
            "## Key Decision Log (3-5 important architectural or technical decisions made, with rationale)\n"
            "## Gotchas & Tech Debt (non-obvious things that will trip up new engineers, known issues, temporary hacks)\n"
            "## Dependency Map (external services, APIs, and libraries the system depends on, with their roles)\n"
            "## Getting Started (step-by-step guide to set up the environment and make a first contribution)\n\n"
            "Target length: 1500+ words. Be specific — name actual files, classes, and functions.\n\n"
            f"File structure:\n{file_structure}\n\n"
            f"Recent checkpoints:\n{recent_checkpoints}\n\n"
            f"Dependency graph:\n{dependency_graph}\n\n"
            f"Class hierarchy:\n{class_hierarchy}"
        )
        content = strip_code_fences(_call_llm(system, user))
        return SimpleNamespace(master_markdown=content)


class PRSummaryGenerator:
    """
    Generates a pull request summary document.
    Replaces DSPy PRSummarySignature + PRSummaryGenerator.
    """
    def __call__(self, pr_title: str, pr_number: str, base_branch: str,
                 head_branch: str, combined_diff: str, commit_checkpoints: str) -> SimpleNamespace:
        system = (
            "You are a senior engineer writing a pull request summary for reviewers and for future reference. "
            "This document should give reviewers everything they need to understand the PR's purpose, scope, and risk "
            "without reading every line of code. It also serves as a historical record of what changed and why. "
            "Target length: 600-1200 words."
        )
        user = (
            f"Write a PR summary for PR #{pr_number}: {pr_title}\n"
            f"Merging {head_branch} into {base_branch}.\n\n"
            "MUST include exactly these sections in order:\n"
            "## Overview (2-3 sentences: what this PR does and why it exists)\n"
            "## Changes by Area (changes grouped by module/concern, with specific file and function names)\n"
            "## Commit Walkthrough (brief summary of each commit's purpose in chronological order)\n"
            "## Architectural Impact (what changes in the system design, data flow, or interfaces)\n"
            "## Review Notes (specific areas reviewers should focus on, potential risks, edge cases to test)\n"
            "## Priority Rating (one of: CRITICAL / HIGH / MEDIUM / LOW with justification)\n\n"
            "Target length: 600-1200 words.\n\n"
            f"Combined diff:\n{combined_diff}\n\n"
            f"Commit checkpoints:\n{commit_checkpoints}"
        )
        content = strip_code_fences(_call_llm(system, user))
        return SimpleNamespace(pr_summary_markdown=content)
