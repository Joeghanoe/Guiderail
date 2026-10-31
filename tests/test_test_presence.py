"""T.1 test-presence check: source changes need a test change; the skip must be named."""
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "harness/tools/code/test-presence.sh"
BUNDLE = ROOT / "harness/tools/harness/bundle.py"


class TestPresenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.repo = pathlib.Path(temp.name)
        self.git("init", "-q")
        self.write("Services/Thing.cs", "namespace D;\npublic class Thing { }\n")
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True)

    def write(self, rel, text="x\n"):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def check(self, skip=None):
        command = ["bash", str(SCRIPT)]
        if skip:
            command = ["env", f"TEST_PRESENCE_SKIP={skip}", *command]
        return subprocess.run(command, cwd=self.repo, capture_output=True, text=True)

    def test_nothing_changed_passes(self):
        self.assertEqual(self.check().returncode, 0)

    def test_source_change_without_a_test_fails_and_names_the_file(self):
        self.write("Services/Thing.cs", "namespace D;\npublic class Thing { public int A() => 1; }\n")
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Services/Thing.cs", result.stderr)

    def test_source_change_with_a_test_passes(self):
        self.write("Services/Thing.cs", "namespace D;\npublic class Thing { public int A() => 1; }\n")
        for rel in ("Tests/ThingTests.cs", "Thing.Tests/Another.cs"):
            self.write(rel, "namespace D;\n")
            self.assertEqual(self.check().returncode, 0, rel)
            (self.repo / rel).unlink()

    def test_a_new_untracked_source_file_needs_a_test_too(self):
        self.write("Services/New.cs", "namespace D;\npublic class New { }\n")
        self.assertEqual(self.check().returncode, 1)

    def test_a_skip_must_be_named_and_is_reported(self):
        self.write("Services/Thing.cs", "// comment only\n")
        result = self.check(skip="comment only change")
        self.assertEqual(result.returncode, 0)
        self.assertIn("comment only change", result.stderr)

    def test_non_csharp_changes_do_not_need_a_test(self):
        self.write("README.md", "docs\n")
        self.assertEqual(self.check().returncode, 0)

    def test_select_brief_prints_one_line_per_rule_and_no_lists(self):
        out = subprocess.run(["python3", "-I", str(BUNDLE), "select", "--brief", "src/A.cs"],
                             capture_output=True, text=True).stdout
        lines = out.strip().splitlines()
        self.assertTrue(lines and all(": " in line for line in lines))
        self.assertTrue(any(line.startswith("T.1: ") for line in lines))
        self.assertNotIn("precedent", out)


if __name__ == "__main__":
    unittest.main()
