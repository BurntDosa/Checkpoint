import unittest
from unittest.mock import MagicMock, patch
import os

# Set dummy env var to pass initial import checks if any
os.environ["GEMINI_API_KEY"] = "dummy_key"

from src.graph import app

class TestCheckpointWorkflow(unittest.TestCase):

    @patch("src.graph.configure_gemini")
    @patch("src.graph.CheckpointGenerator")
    @patch("src.graph.save_checkpoint")
    @patch("src.graph.VectorDB")
    def test_full_workflow(self, mock_vector_db, mock_save, mock_generator_cls, mock_config):
        # Setup Mocks
        
        # Mock Generator
        mock_generator_instance = MagicMock()
        mock_generator_instance.return_value.markdown_content = "# Generated Checkpoint"
        mock_generator_cls.return_value = mock_generator_instance
        
        # Mock Save
        mock_save.return_value = "/path/to/checkpoints/2023-01-01-abcdef.md"
        
        # Mock VectorDB
        mock_db_instance = MagicMock()
        mock_vector_db.return_value = mock_db_instance

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
        
        # 1. Config should check/set env
        mock_config.assert_called_once()
        
        # 2. Generator should be called with diff
        mock_generator_instance.assert_called_once_with(diff_content=initial_state["diff_content"])
        
        # 3. Output should be preserved in state
        self.assertEqual(final_state["generated_markdown"], "# Generated Checkpoint")
        
        # 4. Save should be called
        mock_save.assert_called_once_with("# Generated Checkpoint", "abcdef123456")
        
        # 5. VectorDB should index the content
        mock_db_instance.add_checkpoint.assert_called_once_with(
            checkpoint_id="abcdef123456",
            content="# Generated Checkpoint",
            metadata=initial_state["metadata"]
        )
        
        print("\nTest passed! Workflow successfully simulated.")

if __name__ == "__main__":
    unittest.main()
