"""Regression coverage for the RTK response observed on the installed binary."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "rtk_codex", Path(__file__).resolve().parents[1] / "harness/hooks/rtk-codex.py"
)
rtk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rtk)


class RtkCodexTests(unittest.TestCase):
    def test_legacy_rewrite_gets_explicit_allow(self):
        response = {"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecisionReason": "RTK auto-rewrite",
            "updatedInput": {"command": "rtk git status"},
        }}
        result = json.loads(rtk.adapt(json.dumps(response)))
        self.assertEqual(result["hookSpecificOutput"].pop("permissionDecision"), "allow")
        self.assertEqual(result, response)

    def test_explicit_decisions_are_preserved(self):
        for decision in ("deny", "ask", "allow"):
            response = {"hookSpecificOutput": {
                "permissionDecision": decision, "updatedInput": {"command": "rtk git status"}
            }}
            self.assertEqual(json.loads(rtk.adapt(json.dumps(response))), response)

    def test_no_rewrite_does_not_grant_permission(self):
        for response in ({}, {"hookSpecificOutput": {"additionalContext": "context"}}):
            self.assertEqual(json.loads(rtk.adapt(json.dumps(response))), response)
        self.assertEqual(rtk.adapt(""), "")

    def test_installer_migrates_existing_hook_and_restores_on_uninstall(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / ".codex/hooks.json"
            config.parent.mkdir()
            original = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
                {"type": "command", "command": "rtk hook claude"},
                {"type": "command", "command": "unrelated-hook"},
            ]}]}}
            config.write_text(json.dumps(original))
            env = dict(os.environ, HOME=directory, GOLDEN_PATH_HOME=str(home / ".golden-path-harness"),
                       HARNESS_VSCODE_USER_DIR=str(home / "vscode"))
            installer = Path(__file__).resolve().parents[1] / "install.sh"

            def install(*args):
                subprocess.run(["bash", str(installer), *args], env=env, check=True, capture_output=True)

            install()
            migrated = config.read_text()
            hooks = json.loads(migrated)["hooks"]["PreToolUse"][0]["hooks"]
            self.assertIn("rtk-codex.py", hooks[0]["command"])
            self.assertEqual(hooks[1]["command"], "unrelated-hook")
            self.assertTrue(list(config.parent.glob("hooks.json.bak-harness-*")))
            install()
            self.assertEqual(config.read_text(), migrated)
            install("--uninstall")
            self.assertEqual(json.loads(config.read_text()), original)


if __name__ == "__main__":
    unittest.main()
