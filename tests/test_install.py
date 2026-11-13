"""Installer tests write only to temporary fixture directories, never real skills."""
import importlib.util
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SPEC = importlib.util.spec_from_file_location("micnow_installer", Path(__file__).resolve().parents[1] / "install.py")
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=str(Path(tempfile.gettempdir()).resolve()))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "repo" / "skills" / "micnow-lab"
        self.parent = self.root / "project" / ".agents" / "skills"
        for name in installer.REQUIRED:
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture: " + name, encoding="utf-8")
        self.original = installer.inventory(self.source)

    def install(self, **kwargs):
        return installer.install(self.source, self.parent, **kwargs)

    def test_default_is_read_only_preview(self):
        result = self.install()
        self.assertEqual(result["status"], "preview")
        self.assertEqual(result["action"], "install")
        self.assertFalse(result["changed"])
        self.assertFalse(self.parent.exists())
        self.assertEqual(installer.inventory(self.source), self.original)

    def test_current_bundled_skill_installs_into_temporary_directory(self):
        bundled = Path(__file__).resolve().parents[1] / "skills" / "micnow-lab"
        result = installer.install(bundled, self.parent, apply=True)
        self.assertTrue(result["verified"])
        self.assertEqual(installer.inventory(self.parent / "micnow-lab"), installer.inventory(bundled))
        self.assertEqual(result["status"], "installed")

    def test_deepseek_harness_cli_preview_install_and_repeat(self):
        project = self.root / "deepseek-project"
        project.mkdir()
        target = project / ".dsh" / "skills" / "micnow-lab"
        other = project / ".dsh" / "skills" / "other-skill" / "SKILL.md"
        other.parent.mkdir(parents=True)
        other.write_text("keep this skill", encoding="utf-8")
        args = ["--agent", "deepseek-harness", "--project", str(project)]

        def invoke(extra=()):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(installer.main(args + list(extra)), 0)
            return json.loads(output.getvalue())

        preview = invoke()
        self.assertEqual(preview["status"], "preview")
        self.assertEqual(preview["destination"], str(target))
        self.assertFalse(target.exists())
        result = invoke(["--install"])
        self.assertEqual(result["status"], "installed")
        self.assertTrue(result["verified"])
        self.assertEqual(installer.inventory(target), installer.inventory(installer.SOURCE))
        again = invoke(["--install"])
        self.assertEqual(again["status"], "already-installed")
        self.assertFalse(again["changed"])
        self.assertEqual(other.read_text(), "keep this skill")
        self.assertFalse((project / ".agents").exists())

    def test_install_is_verified_idempotent_and_preserves_other_skills(self):
        other = self.parent / "other-skill" / "SKILL.md"
        other.parent.mkdir(parents=True)
        other.write_text("other", encoding="utf-8")
        result = self.install(apply=True)
        self.assertEqual(result["status"], "installed")
        self.assertTrue(result["verified"])
        self.assertEqual(installer.inventory(self.parent / "micnow-lab"), self.original)
        again = self.install(apply=True)
        self.assertEqual(again["status"], "already-installed")
        self.assertFalse(again["changed"])
        self.assertEqual(other.read_text(), "other")
        self.assertFalse((self.parent.parent / ".micnow-lab-backups").exists())

    def test_update_requires_flag_and_keeps_complete_backup(self):
        self.install(apply=True)
        (self.source / "SKILL.md").write_text("new version", encoding="utf-8")
        preview = self.install(update=True)
        self.assertEqual(preview["action"], "update")
        self.assertTrue(preview["requires_update_flag"])
        with self.assertRaises(installer.InstallError):
            self.install(apply=True)
        self.assertEqual(installer.inventory(self.parent / "micnow-lab"), self.original)
        result = self.install(apply=True, update=True)
        self.assertEqual(result["status"], "updated")
        self.assertEqual(installer.inventory(Path(result["backup"])), self.original)
        self.assertEqual(installer.inventory(self.parent / "micnow-lab"), installer.inventory(self.source))
        self.assertNotIn(Path(result["backup"]), self.parent.iterdir())

    def test_failed_replacement_rolls_back_previous_installation(self):
        self.install(apply=True)
        (self.source / "SKILL.md").write_text("new version", encoding="utf-8")
        rename = installer.os.rename
        def fail_stage(source, destination):
            if Path(source).name.startswith(".micnow-lab-install-"):
                raise OSError("simulated replacement failure")
            return rename(source, destination)
        with mock.patch.object(installer.os, "rename", side_effect=fail_stage):
            with self.assertRaisesRegex(OSError, "simulated replacement"):
                self.install(apply=True, update=True)
        self.assertEqual(installer.inventory(self.parent / "micnow-lab"), self.original)
        self.assertFalse(any(p.name.startswith(".micnow-lab-install-") for p in self.parent.iterdir()))

    def test_failed_post_install_verification_rolls_back(self):
        self.install(apply=True)
        (self.source / "SKILL.md").write_text("new version", encoding="utf-8")
        inventory = installer.inventory
        target = self.parent / "micnow-lab"
        def corrupt_check(directory):
            result = inventory(directory)
            if Path(directory) == target and result["SKILL.md"] == b"new version":
                result["SKILL.md"] = b"simulated mismatch"
            return result
        with mock.patch.object(installer, "inventory", side_effect=corrupt_check):
            with self.assertRaisesRegex(installer.InstallError, "Installed files"):
                self.install(apply=True, update=True)
        self.assertEqual(installer.inventory(target), self.original)

    def test_rejects_traversal_overlap_root_and_wrong_parent(self):
        for destination in (self.root / "a" / ".." / "skills", self.source.parent,
                            self.source / "nested", Path(self.root.anchor), self.root / "micnow-lab"):
            with self.subTest(destination=destination), self.assertRaises(installer.InstallError):
                installer.install(self.source, destination, apply=True)
        bad = self.root / "file"
        bad.write_text("keep", encoding="utf-8")
        with self.assertRaises(installer.InstallError):
            installer.install(self.source, bad, apply=True)
        self.assertEqual(bad.read_text(), "keep")

    def test_rejects_symlinks_without_modifying_their_targets(self):
        victim = self.root / "victim"
        victim.mkdir()
        marker = victim / "marker"
        marker.write_text("keep", encoding="utf-8")
        linked_parent = self.root / "linked"
        linked_parent.symlink_to(victim, target_is_directory=True)
        with self.assertRaises(installer.InstallError):
            installer.install(self.source, linked_parent / "skills", apply=True)
        self.parent.mkdir(parents=True)
        (self.parent / "micnow-lab").symlink_to(victim, target_is_directory=True)
        with self.assertRaises(installer.InstallError):
            self.install(apply=True, update=True)
        (self.source / "scripts" / "linked.py").symlink_to(marker)
        with self.assertRaises(installer.InstallError):
            installer.inventory(self.source)
        self.assertEqual(marker.read_text(), "keep")

    def test_refuses_credentials_and_unknown_files_without_reading_them(self):
        credential = self.source / ".env"
        credential.write_text("fixture credential; must not be read", encoding="utf-8")
        read = installer.read_regular_file
        def watch(path):
            self.assertNotEqual(Path(path), credential)
            return read(path)
        with mock.patch.object(installer, "read_regular_file", side_effect=watch):
            with self.assertRaisesRegex(installer.InstallError, "not read"):
                self.install()
        self.assertFalse(self.parent.exists())

    def test_project_and_user_agent_paths_use_only_fixture_home(self):
        project = self.root / "project"
        project.mkdir()
        fake_home = self.root / "home"
        fake_home.mkdir()
        with mock.patch.object(installer.Path, "home", return_value=fake_home), \
                mock.patch.dict(installer.os.environ, {"DSH_HOME": ""}):
            for agent in ("codex", "cursor", "gemini", "qwen-code", "kimi-cli"):
                self.assertEqual(installer.resolve_destination(agent), fake_home / ".agents" / "skills")
                self.assertEqual(installer.resolve_destination(agent, project), project / ".agents" / "skills")
            self.assertEqual(installer.resolve_destination("claude-code"), fake_home / ".claude" / "skills")
            self.assertEqual(installer.resolve_destination("claude-code", project), project / ".claude" / "skills")
            self.assertEqual(installer.resolve_destination("deepseek-harness"), fake_home / ".dsh" / "skills")
            self.assertEqual(installer.resolve_destination("deepseek-harness", project), project / ".dsh" / "skills")
            self.assertEqual(installer.resolve_destination("workbuddy", project), project / ".codebuddy" / "skills")
            with self.assertRaises(installer.InstallError):
                installer.resolve_destination("workbuddy")

    def test_deepseek_harness_custom_home_installs_without_using_real_home(self):
        custom_home = self.root / "custom-dsh-home"
        project = self.root / "project"
        project.mkdir()
        with mock.patch.dict(installer.os.environ, {"DSH_HOME": str(custom_home)}), \
                mock.patch.object(installer.Path, "home", side_effect=AssertionError("Must not consult user home")):
            parent = installer.resolve_destination("deepseek-harness")
            self.assertEqual(parent, custom_home / "skills")
            self.assertEqual(installer.resolve_destination("deepseek-harness", project), project / ".dsh" / "skills")
            result = installer.install(installer.SOURCE, parent, apply=True)
            self.assertTrue(result["verified"])
            self.assertEqual(installer.inventory(parent / "micnow-lab"), installer.inventory(installer.SOURCE))

    def test_deepseek_harness_custom_home_rejects_symlinks_and_traversal(self):
        target = self.root / "keep"
        target.mkdir()
        linked = self.root / "linked-dsh-home"
        linked.symlink_to(target, target_is_directory=True)
        for value in (str(linked), str(self.root / "a" / ".." / "dsh")):
            with self.subTest(home=value), \
                    mock.patch.dict(installer.os.environ, {"DSH_HOME": value}), \
                    self.assertRaises(installer.InstallError):
                installer.resolve_destination("deepseek-harness")
        self.assertEqual(list(target.iterdir()), [])

    def test_explicit_destination_supports_unknown_agent_without_guessing(self):
        explicit = self.root / "custom" / "skills"
        self.assertEqual(installer.resolve_destination(destination=explicit), explicit)
        self.assertEqual(installer.resolve_destination("workbuddy", destination=explicit), explicit)
        for kwargs in ({}, {"agent": "codex", "scope": "project"},
                       {"agent": "codex", "project": self.root, "scope": "user"},
                       {"destination": explicit, "project": self.root}):
            with self.subTest(kwargs=kwargs), self.assertRaises(installer.InstallError):
                installer.resolve_destination(**kwargs)
        self.assertFalse(explicit.exists())


if __name__ == "__main__":
    unittest.main()
