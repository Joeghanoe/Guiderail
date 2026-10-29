"""Adapters are exercised against stand-in CLIs; no provider is called."""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ADAPTERS = ROOT / "harness/tools/testing/adapters"
FIXTURES = pathlib.Path(__file__).parent / "fixtures"


class AdapterTests(unittest.TestCase):
    def invoke(self, adapter, fake, *extra, model="m-1"):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = pathlib.Path(temp.name)
        (root / "ws").mkdir()
        (root / "trace").mkdir()
        (root / "prompt.txt").write_text("do the task", encoding="utf-8")
        command = [sys.executable, str(ADAPTERS / adapter), "--workspace", str(root / "ws"), "--prompt-file", str(root / "prompt.txt"),
                   "--trace-dir", str(root / "trace"), "--executable", str(FIXTURES / fake), *extra]
        if model:
            command += ["--model", model]
        run = subprocess.run(command, capture_output=True, text=True)
        return run, root

    def test_claude_adapter_pins_model_restricts_tools_and_reports_usage(self):
        run, root = self.invoke("claude_code.py", "fake_claude.py", "--deny-path", "D:\Prototypes\TV", model="claude-sonnet-5-5")
        self.assertEqual(run.returncode, 0, run.stderr)
        seen = json.loads((root / "ws/seen.json").read_text(encoding="utf-8"))
        argv = seen["argv"]
        self.assertEqual(seen["prompt"], "do the task")
        self.assertEqual(argv[argv.index("--model") + 1], "claude-sonnet-5-5")
        self.assertEqual(argv[argv.index("--setting-sources") + 1], "project")
        self.assertNotIn("--dangerously-skip-permissions", argv)
        self.assertIn("Read(/d/Prototypes/TV/**)", argv)
        usage = json.loads((root / "trace/usage.json").read_text(encoding="utf-8"))
        self.assertEqual((usage["input_tokens"], usage["output_tokens"], usage["cost"], usage["tool_calls"]), (100, 20, 0.5, 1))
        self.assertTrue((root / "trace/claude-events.jsonl").is_file())

    def test_codex_adapter_sandboxes_and_sums_turn_usage(self):
        run, root = self.invoke("codex.py", "fake_codex.py")
        self.assertEqual(run.returncode, 0, run.stderr)
        argv = json.loads((root / "ws/seen.json").read_text(encoding="utf-8"))["argv"]
        self.assertEqual(argv[argv.index("-s") + 1], "workspace-write")
        self.assertEqual(argv[argv.index("-m") + 1], "m-1")
        self.assertIn("--ignore-user-config", argv)
        usage = json.loads((root / "trace/usage.json").read_text(encoding="utf-8"))
        self.assertEqual((usage["input_tokens"], usage["output_tokens"], usage["tool_calls"], usage["turns"]), (12, 4, 1, 2))
        self.assertIsNone(usage["cost"])

    def test_a_model_is_required(self):
        run, _ = self.invoke("claude_code.py", "fake_claude.py", model=None)
        self.assertNotEqual(run.returncode, 0)


if __name__ == "__main__":
    unittest.main()
