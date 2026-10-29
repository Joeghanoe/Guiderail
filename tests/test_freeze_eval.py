import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("freeze_eval", ROOT / "harness/tools/testing/freeze_eval.py")
freeze_eval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(freeze_eval)


class FreezeTests(unittest.TestCase):
    def test_snapshot_detects_changes_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            source = root / "source.txt"
            source.write_text("approved")
            spec = {"approval": "test approval", "harness_commit": "test",
                    "files": [{"source": str(source), "path": "candidate/task.md"}]}
            frozen = root / "frozen"
            freeze_eval.freeze(spec, frozen)
            source.write_text("later edits")
            self.assertEqual(freeze_eval.verify(frozen), [])
            with self.assertRaises(ValueError):
                freeze_eval.freeze(spec, frozen)
            (frozen / "candidate/task.md").write_text("tampered")
            self.assertEqual(freeze_eval.verify(frozen), ["candidate/task.md"])

    def test_paths_and_collisions_are_rejected_before_writing(self):
        for names in (("../escape",), ("freeze.json",), ("a", "a"), ("a", "a/b")):
            with self.subTest(names=names), tempfile.TemporaryDirectory() as tmp:
                root = pathlib.Path(tmp)
                source = root / "source"
                source.write_text("data")
                spec = {"approval": "test", "harness_commit": "test",
                        "files": [{"source": str(source), "path": n} for n in names]}
                with self.assertRaises(ValueError):
                    freeze_eval.freeze(spec, root / "out")
                self.assertFalse((root / "out").exists())

    def test_extra_files_do_not_silently_enter_the_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            source = root / "source"
            source.write_text("task")
            frozen = root / "frozen"
            freeze_eval.freeze({"approval": "test", "harness_commit": "test",
                                "files": [{"source": str(source), "path": "task.md"}]}, frozen)
            (frozen / "unexpected.txt").write_text("leaked implementation")
            self.assertEqual(freeze_eval.verify(frozen), ["unexpected.txt"])

    def test_manifest_changes_require_a_new_trusted_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            source = root / "source"
            source.write_text("task")
            frozen = root / "frozen"
            freeze_eval.freeze({"approval": "test", "harness_commit": "test",
                                "files": [{"source": str(source), "path": "task.md"}]}, frozen)
            expected = freeze_eval.sha(frozen / "freeze.json")
            self.assertEqual(freeze_eval.verify(frozen, expected), [])
            (frozen / "freeze.json").write_text('{}')
            self.assertEqual(freeze_eval.verify(frozen, expected), ["freeze.json"])


if __name__ == "__main__":
    unittest.main()
