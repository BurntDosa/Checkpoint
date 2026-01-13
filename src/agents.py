import dspy

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

class CheckpointGenerator(dspy.Module):
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

# --- New Agents for Advanced Workflows ---

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
        return self.summarizer(
            checkpoints_content=checkpoints_content,
            user_last_active_date=user_last_active_date
        )

class OnboardingSynthesizer(dspy.Signature):
    """
    Generates a 'Master Context' document for a new developer (The Map).
    Explains architecture, key decisions, gotchas, and dependencies basically telling the 'Story' of the codebase.
    """
    file_structure = dspy.InputField(desc="The file tree structure of the repository.")
    recent_checkpoints = dspy.InputField(desc="Recent high-level checkpoints to understand history.")
    
    master_markdown = dspy.OutputField(desc="A comprehensive guide. Sections: Architectural Overview, Key Decision Log, Gotchas & Tech Debt, Dependency Map.")

class MasterContextGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.synthesizer = dspy.ChainOfThought(OnboardingSynthesizer)
        
    def forward(self, file_structure, recent_checkpoints):
        return self.synthesizer(
            file_structure=file_structure,
            recent_checkpoints=recent_checkpoints
        )
