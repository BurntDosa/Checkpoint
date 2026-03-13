import unittest
from unittest.mock import MagicMock, patch
import os

# Set dummy env var to pass initial import checks if any
os.environ["MISTRAL_API_KEY"] = "dummy_key"

from checkpoint_agent.graph import app

class TestCheckpointWorkflow(unittest.TestCase):

    @patch("checkpoint_agent.graph.CheckpointGenerator")
    @patch("checkpoint_agent.graph.save_checkpoint")
    def test_full_workflow(self, mock_save, mock_generator_cls):
        # Setup Mocks

        # Mock Generator
        mock_generator_instance = MagicMock()
        mock_generator_instance.return_value.markdown_content = "# Generated Checkpoint"
        mock_generator_cls.return_value = mock_generator_instance

        # Mock Save
        mock_save.return_value = "/path/to/checkpoints/2023-01-01-abcdef.md"

        # Initial State
        initial_state = {
            "diff_content": "diff --git a/file.py b/file.py...",
            "commit_hash": "abcdef123456",
            "metadata": {"author": "Test User", "message": "Test commit"},
            "generated_markdown": None,
            "filepath": None
        }

        # Execute Workflow
        final_state = app.invoke(initial_state)

        # Assertions

        # 1. Generator should be called with diff + metadata
        mock_generator_instance.assert_called_once_with(
            diff_content=initial_state["diff_content"],
            commit_message="Test commit",
            author="Test User",
            date="",
        )

        # 2. Output should be preserved in state
        self.assertEqual(final_state["generated_markdown"], "# Generated Checkpoint")

        # 3. Save should be called
        mock_save.assert_called_once_with("# Generated Checkpoint", "abcdef123456", author="Test User")

        print("\nTest passed! Workflow successfully simulated.")

if __name__ == "__main__":
    unittest.main()
