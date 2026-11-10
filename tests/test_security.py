import contextlib
import datetime
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

from checkpoint_agent import file_io, storage
from checkpoint_agent import git_hook_installer as hooks


@unittest.skipUnless(os.name == "posix", "Security filesystem fixes target macOS/Linux")
class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        cwd = Path.cwd()
        os.chdir(self.repo)
        self.addCleanup(os.chdir, cwd)
        self.private = self.root / "private.md"
        self.private.write_text("OUTSIDE_PRIVATE_MARKER", encoding="utf-8")

    def link(self, destination, target, directory=False):
        destination.symlink_to(target, target_is_directory=directory)

    def onboard(self):
        from checkpoint_agent.__main__ import main
        (self.repo / ".checkpoint.yaml").write_text(json.dumps({"features": {"diagrams": False}}))
        with patch.dict(os.environ, {"MISTRAL_API_KEY": "dummy-not-a-key"}), \
                patch("sys.argv", ["checkpoint", "--onboard"]), \
                patch("checkpoint_agent.agents._call_llm", return_value="# Fixture document") as model, \
                contextlib.redirect_stdout(io.StringIO()):
            main()
        return model

    def test_context_links_are_not_sent_to_model(self):
        for name in ["README.md", "pyproject.toml", "package.json", "requirements.txt"]:
            with self.subTest(name=name):
                path = self.repo / name
                self.link(path, self.private)
                model = self.onboard()
                self.assertTrue(model.called)
                self.assertNotIn("OUTSIDE_PRIVATE_MARKER", model.call_args.args[1])
                path.unlink()
        (self.repo / "README.md").write_text("LEGITIMATE_README")
        self.assertIn("LEGITIMATE_README", self.onboard().call_args.args[1])

    def test_linked_stored_context_is_skipped(self):
        (self.repo / "checkpoints").mkdir()
        self.link(self.repo / "checkpoints/Checkpoint-A.md", self.private)
        self.assertNotIn("OUTSIDE_PRIVATE_MARKER", self.onboard().call_args.args[1])
        self.assertEqual(storage.get_checkpoints_since(datetime.datetime(2000, 1, 1)), [])
        (self.repo / "catchups").mkdir()
        self.link(Path(storage.get_catchup_path("a@example.invalid")), self.private)
        self.assertIsNone(storage.get_existing_catchup("a@example.invalid"))

    def test_sample_and_ast_inputs_do_not_follow_links(self):
        from checkpoint_agent.llm_diagrams import get_sample_files
        from checkpoint_agent.mermaid_utils import generate_all_mermaid_diagrams
        self.private.write_text("import OUTSIDE_PRIVATE_MARKER\n")
        self.link(self.repo / "main.py", self.private)
        (self.repo / "app.py").write_text("import ordinary_module\n")
        self.assertNotIn("OUTSIDE_PRIVATE_MARKER", get_sample_files())
        self.assertIn("ordinary_module", get_sample_files())
        self.assertNotIn("OUTSIDE_PRIVATE_MARKER", str(generate_all_mermaid_diagrams(".")))

    def test_all_document_writers_reject_linked_leaves(self):
        (self.repo / "checkpoints").mkdir()
        (self.repo / "catchups").mkdir()
        writers = [
            ("MASTER_CONTEXT.md", lambda: storage.save_master_context("replacement")),
            ("checkpoints/Checkpoint-A.md", lambda: storage.save_checkpoint("replacement", "abcdef0", "A")),
            ("checkpoints/PR-1-feature.md", lambda: storage.save_pr_summary("replacement", "1", "feature")),
            (storage.get_catchup_path("a@example.invalid"), lambda: storage.save_catchup("replacement", "a@example.invalid")),
        ]
        for name, write in writers:
            with self.subTest(name=name):
                self.link(Path(name), self.private)
                with self.assertRaises(OSError):
                    write()
                self.assertEqual(self.private.read_text(), "OUTSIDE_PRIVATE_MARKER")

    def test_parent_links_block_reads_writes_creation_and_deletion(self):
        outside = self.root / "outside"
        outside.mkdir()
        marker = outside / "marker.md"
        marker.write_text("outside")
        self.link(self.repo / "linked", outside, directory=True)
        for operation in [lambda: file_io.read_text("linked/marker.md"),
                          lambda: file_io.write_text("linked/marker.md", "bad"),
                          lambda: file_io.make_directory("linked/new"),
                          lambda: file_io.remove_file("linked/marker.md")]:
            with self.assertRaises(OSError):
                operation()
        self.assertEqual(marker.read_text(), "outside")
        self.assertFalse((outside / "new").exists())


    def test_dangling_output_link_does_not_create_its_target(self):
        missing = self.root / "missing.md"
        self.link(self.repo / "MASTER_CONTEXT.md", missing)
        with self.assertRaises(OSError):
            storage.save_master_context("bad")
        self.assertFalse(missing.exists())

    def test_initialization_leaves_existing_master_context_link_untouched(self):
        from checkpoint_agent.__main__ import install_ci_workflow
        missing = self.root / "missing.md"
        self.link(self.repo / "MASTER_CONTEXT.md", missing)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(install_ci_workflow())
        self.assertFalse(missing.exists())

    def test_regular_outputs_external_locations_and_prepend_remain_supported(self):
        location = self.root / "external"
        location.mkdir()
        for name in [location / "a", Path("../external/relative.md"), location / "名称😀.md"]:
            self.assertEqual(storage.save_master_context("document", str(name)), os.path.abspath(name))
            self.assertEqual(file_io.read_text(name), "document")
        storage.save_checkpoint("first", "aaaaaaa", "A")
        storage.save_checkpoint("second", "bbbbbbb", "A")
        text = file_io.read_text("checkpoints/Checkpoint-A.md")
        self.assertLess(text.index("second"), text.index("first"))
        storage.save_catchup("catchup", "a@example.invalid", str(location))
        self.assertEqual(storage.get_existing_catchup("a@example.invalid", str(location)), "catchup")
        self.assertTrue(storage.delete_catchup("a@example.invalid", str(location)))
        self.assertFalse(storage.delete_catchup("a@example.invalid", str(location)))

    def test_macos_system_alias_accepts_regular_files(self):
        if sys.platform != "darwin":
            self.skipTest("macOS system alias test")
        path = self.repo / "alias.md"
        if not str(path).startswith("/private/var/"):
            self.skipTest("Fixture is not under the /var system alias")
        alias = Path(str(path).removeprefix("/private"))
        file_io.write_text(alias, "regular")
        self.assertEqual(file_io.read_text(alias), "regular")

    def test_existing_file_identity_and_permissions_are_preserved(self):
        file_io.write_text("document.md", "original")
        before = Path("document.md").stat()
        file_io.write_text("document.md", "replacement")
        after = Path("document.md").stat()
        self.assertEqual((before.st_dev, before.st_ino), (after.st_dev, after.st_ino))
        self.assertEqual(before.st_mode, after.st_mode)

    def test_secret_update_preserves_restrictive_permissions(self):
        from checkpoint_agent.config import set_api_key_env
        secret = Path(".env")
        secret.write_text("MISTRAL_API_KEY=old-dummy\n")
        secret.chmod(0o600)
        before = secret.stat()
        with patch.dict(os.environ):
            set_api_key_env("mistral", "new-dummy")
        after = secret.stat()
        self.assertEqual((before.st_dev, before.st_ino, before.st_mode),
                         (after.st_dev, after.st_ino, after.st_mode))
        self.assertIn("MISTRAL_API_KEY=new-dummy", secret.read_text())


    def test_output_hardlink_does_not_overwrite_outside_inode(self):
        os.link(self.private, "document.md")
        with self.assertRaises(OSError):
            file_io.write_text("document.md", "replacement")
        self.assertEqual(self.private.read_text(), "OUTSIDE_PRIVATE_MARKER")
        self.assertEqual(file_io.read_text("document.md"), "OUTSIDE_PRIVATE_MARKER")

    def test_parent_swap_cannot_redirect_opened_directory(self):
        nested = self.repo / "nested"
        nested.mkdir()
        (nested / "input.md").write_text("safe")
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "input.md").write_text("private")
        original = os.open
        def swap(name, flags, *args, **kwargs):
            if name == "input.md":
                nested.rename(self.repo / "moved")
                nested.symlink_to(outside, target_is_directory=True)
            return original(name, flags, *args, **kwargs)
        with patch("checkpoint_agent.file_io.os.open", side_effect=swap):
            self.assertEqual(file_io.read_text("nested/input.md"), "safe")

    def test_leaf_swap_before_truncation_never_writes_outside(self):
        file_io.write_text("document.md", "original")
        original = os.ftruncate
        def swap(fd, size):
            Path("document.md").unlink()
            self.link(Path("document.md"), self.private)
            return original(fd, size)
        with patch("os.ftruncate", side_effect=swap):
            file_io.write_text("document.md", "replacement")
        self.assertEqual(self.private.read_text(), "OUTSIDE_PRIVATE_MARKER")
        if not Path("document.md").is_symlink():
            self.assertEqual(file_io.read_text("document.md"), "replacement")

    def test_hooks_never_select_repository_main_and_upgrade_known_legacy(self):
        (self.repo / ".git/hooks").mkdir(parents=True)
        (self.repo / ".venv/bin").mkdir(parents=True)
        (self.repo / ".venv/bin/python").write_text("dummy")
        (self.repo / "main.py").write_text("raise RuntimeError('must not run')")
        template = hooks.get_prepush_hook_template(True, self.repo)
        self.assertIn("checkpoint --commit", template)
        self.assertIn("checkpoint --catchup-all", template)
        self.assertNotIn(str(self.repo / "main.py"), template)
        old_command = f'"{self.repo / ".venv/bin/python"}" "{self.repo / "main.py"}"'
        prefix = "#!/bin/sh\n# existing user hook\n\n"
        hook = self.repo / ".git/hooks/pre-push"
        hook.write_text(prefix + template.replace("checkpoint --", old_command + " --"))
        backup = hook.with_name("pre-push.checkpoint-backup")
        backup.write_text("original user hook")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(hooks.install_hook(auto_catchup=True))
        self.assertEqual(hook.read_text(), prefix + template)
        self.assertEqual(backup.read_text(), "original user hook")
        customized = template + "\n# manual customization\n"
        hook.write_text(customized)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(hooks.install_hook())
        self.assertEqual(hook.read_text(), customized)

    def test_workflow_values_stay_data_and_all_scripts_parse(self):
        source = Path(__file__).resolve().parents[1]
        bash = shutil.which("bash")
        self.assertIsNotNone(bash, "Bash is required to validate shipped workflow scripts")
        payload = "audit$(touch${IFS}executed)"
        prelude = '''git() { printf '%s\\0' "$@" >> args.bin; }
checkpoint() { printf '%s\\0' "$@" >> args.bin; }
'''
        for name in ["checkpoint_agent/templates/checkpoint.yml", ".github/workflows/checkpoint.yml", ".github/workflows/publish.yml"]:
            workflow = yaml.safe_load((source / name).read_text())
            for job in workflow["jobs"].values():
                for step in job["steps"]:
                    if "run" not in step:
                        continue
                    script = step["run"]
                    self.assertNotIn("${{", script)
                    syntax = subprocess.run([bash, "-n"], input=script, capture_output=True, text=True)
                    self.assertEqual(syntax.returncode, 0, syntax.stderr)
                    if not any(key in step.get("env", {}) for key in ["HEAD_BRANCH", "REF_NAME", "BASE_BRANCH", "TAG"]):
                        continue
                    env = dict(os.environ)
                    for key in step["env"]:
                        env[key] = payload if key in {"HEAD_BRANCH", "REF_NAME", "BASE_BRANCH", "PUSH_REF"} else "1"
                    env["PR_TITLE"] = "title$(touch executed) \" ' literal"
                    env["TAG"] = "v" + payload
                    dist = self.repo / "dist"
                    dist.mkdir(exist_ok=True)
                    (dist / (payload + ".whl")).touch()
                    run = subprocess.run([bash, "-e", "-c", prelude + script], env=env, capture_output=True, text=True)
                    self.assertEqual(run.returncode, 0, run.stderr)
                    self.assertFalse(Path("executed").exists())
                    if "HEAD_BRANCH" in step["env"] and "git pull" in script:
                        self.assertIn(payload.encode(), Path("args.bin").read_bytes().split(b"\0"))


if __name__ == "__main__":
    unittest.main()
