from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import git

from checkpoint_agent.agents import CheckpointGenerator
from checkpoint_agent.git_utils import get_diff, get_diff_between_refs, get_repo


class PromptTests(unittest.TestCase):
    def test_context_qualifies_only_guesses_and_preserves_impact_rule(self):
        rule = (
            "- State why a change was made directly when the commit message or diff shows the reason. "
            "For a genuine guess, qualify it once inside the sentence (for example, 'probably'), "
            "never as a sentence prefix.\n"
        )
        with patch("checkpoint_agent.agents._call_llm", return_value="## Context\nFixture") as model:
            CheckpointGenerator()("fixture diff", commit_message="Fix filenames")
        system, user = model.call_args.args
        self.assertIn(rule, system)
        self.assertNotIn("prefix with 'Likely' or 'Appears to'", system)
        self.assertIn("mark inferred impacts with 'Likely:'", user)


class DiffTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.repo = git.Repo.init(self.root)
        self.addCleanup(self.repo.close)
        self.addCleanup(get_repo.cache_clear)
        self.actor = git.Actor("Fixture", "fixture@example.invalid")
        self.system_paths = [
            ".checkpoint.yaml", ".github/workflows/checkpoint.yml",
            "checkpoints/fixture.md", "catchups/fixture.md", "MASTER_CONTEXT.md",
        ]
        for name in ["modified.txt", "deleted.txt", "old.txt"] + self.system_paths:
            self.write(name, f"original {name}\n")
        self.base = self.commit("Initial fixture")
        self.write("added.txt", "new file\n")
        self.write("modified.txt", "updated file\n")
        (self.root / "deleted.txt").unlink()
        (self.root / "old.txt").rename(self.root / "renamed.txt")
        for name in self.system_paths:
            self.write(name, "CHECKPOINT_SYSTEM_SECRET\n")
        self.head = self.commit("Change fixture files")
        self.diff = get_diff(self.head.hexsha, str(self.root))

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def commit(self, message):
        self.repo.git.add(A=True)
        return self.repo.index.commit(message, author=self.actor, committer=self.actor)

    def test_added_file(self):
        self.assertIn(
            "diff --git a/added.txt b/added.txt\n--- /dev/null\n+++ b/added.txt\n@@", self.diff
        )
        self.assertIn("+new file\n", self.diff)

    def test_modified_file(self):
        self.assertIn(
            "diff --git a/modified.txt b/modified.txt\n--- a/modified.txt\n+++ b/modified.txt\n@@",
            self.diff,
        )
        self.assertIn("-original modified.txt\n+updated file\n", self.diff)

    def test_pure_rename(self):
        self.assertIn(
            "diff --git a/old.txt b/renamed.txt\n--- a/old.txt\n+++ b/renamed.txt\n", self.diff
        )

    def test_deleted_file(self):
        self.assertIn(
            "diff --git a/deleted.txt b/deleted.txt\n--- a/deleted.txt\n+++ /dev/null\n@@", self.diff
        )
        self.assertIn("-original deleted.txt\n", self.diff)

    def test_root_commit(self):
        diff = get_diff(self.base.hexsha, str(self.root))
        self.assertIn(
            "diff --git a/modified.txt b/modified.txt\n--- /dev/null\n+++ b/modified.txt\n@@", diff
        )
        self.assertIn("+original modified.txt\n", diff)

    def test_system_files_remain_excluded(self):
        for name in self.system_paths:
            with self.subTest(path=name):
                self.assertNotIn(name, self.diff)
        self.assertNotIn("CHECKPOINT_SYSTEM_SECRET", self.diff)

    def test_between_refs_already_includes_headers_and_excludes_system_files(self):
        diff = get_diff_between_refs(self.base.hexsha, self.head.hexsha, str(self.root))
        for old, new, source, target in [
            ("added.txt", "added.txt", "/dev/null", "b/added.txt"),
            ("modified.txt", "modified.txt", "a/modified.txt", "b/modified.txt"),
            ("deleted.txt", "deleted.txt", "a/deleted.txt", "/dev/null"),
        ]:
            with self.subTest(path=new):
                self.assertIn(f"diff --git a/{old} b/{new}\n", diff)
                self.assertIn(f"--- {source}\n+++ {target}\n@@", diff)
        self.assertIn("diff --git a/old.txt b/renamed.txt\n", diff)
        self.assertIn("rename from old.txt\nrename to renamed.txt", diff)
        for name in self.system_paths:
            self.assertNotIn(name, diff)
        self.assertNotIn("CHECKPOINT_SYSTEM_SECRET", diff)
