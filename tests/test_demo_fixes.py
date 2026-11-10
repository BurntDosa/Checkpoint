from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

from checkpoint_agent.config import load_config
from checkpoint_agent.storage import _filter_entries_after, save_checkpoint
from checkpoint_agent.__main__ import install_ci_workflow


class DemoFixTests(unittest.TestCase):
    def test_config_expands_environment_model(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / '.checkpoint.yaml'
            path.write_text('llm:\n  model: ${CHECKPOINT_MODEL}\n')
            with patch.dict('os.environ', {'CHECKPOINT_MODEL': 'gpt-6-luna'}):
                self.assertEqual(load_config(str(path)).llm.model, 'gpt-6-luna')

    def test_checkpoint_uses_commit_calendar_date_for_catchup(self):
        with tempfile.TemporaryDirectory() as root, patch('checkpoint_agent.storage.CHECKPOINT_DIR', root):
            path = save_checkpoint('changed code', 'abcdef0123', 'Ava', '2026-10-02T00:19:00+05:30')
            content = Path(path).read_text()
            self.assertIn('2026-10-02', content)
            self.assertIn('changed code', _filter_entries_after(content, datetime(2026, 10, 2, 0, 19, tzinfo=timezone(timedelta(hours=5, minutes=30)))))
            save_checkpoint('changed code', 'abcdef0123', 'Ava', '2026-10-02T00:19:00+05:30')
            self.assertEqual(Path(path).read_text(), content)
            save_checkpoint('updated analysis', 'abcdef0123', 'Ava', '2026-10-02T00:19:00+05:30')
            self.assertEqual(Path(path).read_text().count('## Commit'), 1)
            self.assertIn('updated analysis', Path(path).read_text())

    def test_init_does_not_write_placeholder(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertTrue(install_ci_workflow(root))
            self.assertFalse((Path(root) / 'MASTER_CONTEXT.md').exists())

    def test_workflow_has_backfill_and_pr_events(self):
        workflow = yaml.safe_load((Path(__file__).parents[1] / 'checkpoint_agent/templates/checkpoint.yml').read_text())
        events = workflow.get('on', workflow.get(True))
        self.assertIn('backfill', events['workflow_dispatch']['inputs'])
        self.assertEqual(events['pull_request']['types'], ['opened', 'synchronize', 'reopened', 'closed'])
        script = workflow['jobs']['checkpoint-push']['steps'][4]['run']
        self.assertIn('git merge-base', script)
        self.assertIn('git log --reverse', script)
        self.assertIn('checkpoint-bot@users.noreply.github.com', script)


if __name__ == '__main__':
    unittest.main()
