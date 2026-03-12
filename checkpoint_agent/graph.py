from checkpoint_agent.agents import CheckpointGenerator
from checkpoint_agent.storage import save_checkpoint


def run_pipeline(diff_content: str, commit_hash: str, metadata: dict) -> dict:
    generator = CheckpointGenerator()
    result = generator(diff_content=diff_content)

    author = metadata.get("author", "Unknown")
    filepath = save_checkpoint(result.markdown_content, commit_hash, author=author)

    return {
        "diff_content": diff_content,
        "commit_hash": commit_hash,
        "metadata": metadata,
        "generated_markdown": result.markdown_content,
        "filepath": filepath,
    }


class _App:
    def invoke(self, state: dict, config=None, **kwargs) -> dict:
        return run_pipeline(
            diff_content=state["diff_content"],
            commit_hash=state["commit_hash"],
            metadata=state["metadata"],
        )


app = _App()
