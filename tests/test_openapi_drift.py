"""DEL.5: the drift check ignores formatting, reports added and removed operations, and fails on a stale snapshot."""
import json
import pathlib
import subprocess
import tempfile
import unittest

TOOL = pathlib.Path(__file__).resolve().parents[1] / "harness" / "tools" / "code" / "openapi-drift.py"


def doc(*operations, version="1.0.0", extra=None):
    paths = {}
    for operation in operations:
        method, route = operation.split(" ", 1)
        paths.setdefault(route, {})[method.lower()] = {"operationId": operation, "responses": {"200": {"description": "ok"}}}
    result = {"openapi": "3.0.1", "info": {"title": "t", "version": version}, "paths": paths}
    result.update(extra or {})
    return result


class OpenApiDriftTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = pathlib.Path(temp.name)

    def run_tool(self, generated, committed, *flags, generated_text=None):
        (self.dir / "generated.json").write_text(generated_text or json.dumps(generated), encoding="utf-8")
        (self.dir / "committed.json").write_text(json.dumps(committed, indent=4), encoding="utf-8")
        return subprocess.run(["python3", "-I", str(TOOL), "--generated", str(self.dir / "generated.json"),
                               "--committed", str(self.dir / "committed.json"), *flags], capture_output=True, text=True)

    def test_equal_documents_pass_whatever_the_formatting_and_key_order(self):
        committed = doc("GET /a", "POST /b")
        shuffled = json.dumps(dict(reversed(list(committed.items()))), separators=(",", ":"))
        result = self.run_tool(None, committed, generated_text=shuffled)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_an_added_operation_is_reported(self):
        result = self.run_tool(doc("GET /a", "POST /b"), doc("GET /a"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("added:   POST /b", result.stdout)
        self.assertIn("regenerate", result.stdout.lower())

    def test_a_removed_operation_is_called_a_breaking_change(self):
        result = self.run_tool(doc("GET /a"), doc("GET /a", "DELETE /a"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("removed: DELETE /a", result.stdout)
        self.assertIn("breaking", result.stdout)

    def test_a_changed_schema_with_the_same_operations_is_still_drift(self):
        result = self.run_tool(doc("GET /a", extra={"components": {"schemas": {"X": {"type": "string"}}}}), doc("GET /a"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("same", result.stdout)

    def test_a_version_bump_alone_fails_unless_it_is_ignored(self):
        self.assertEqual(self.run_tool(doc("GET /a", version="2.0.0"), doc("GET /a")).returncode, 1)
        self.assertEqual(self.run_tool(doc("GET /a", version="2.0.0"), doc("GET /a"), "--ignore-version").returncode, 0)

    def test_an_unreadable_file_fails(self):
        result = self.run_tool(None, doc("GET /a"), generated_text="not json")
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot read", result.stderr)


if __name__ == "__main__":
    unittest.main()
