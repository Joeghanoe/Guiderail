"""Positive and mutation controls exercise the grader without a model or cloud account."""
import importlib.util
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("backup_eval", ROOT / "harness/tools/testing/backup_eval.py")
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)
CONTROL = pathlib.Path(__file__).parent / "fixtures/backup_control.py"


class BackupEvaluationTests(unittest.TestCase):
    def grader(self, root, defect="none"):
        return evaluation.Grader([sys.executable, str(CONTROL), defect], root)

    def test_positive_control_passes_functionality_but_not_unobserved_policy(self):
        with tempfile.TemporaryDirectory() as temp:
            report = self.grader(temp).run()
            self.assertEqual(report["functional_status"], "pass", report["checks"])
            self.assertEqual(report["status"], "inconclusive")
            self.assertEqual(report["policy"]["status"], "inconclusive")
            self.assertEqual(report["hard_gate_violations"], [])
            self.assertIsNone(report["cost"])

    def test_mutations_are_detected_by_the_relevant_criterion(self):
        for defect, check in [("git-history", "f01"), ("source-dependent", "f02"),
                              ("source-mutation", "f03"), ("overwrite", "f03"),
                              ("false-success", "f04"), ("versions", "f05"),
                              ("schedule", "f06"), ("retention", "f06"),
                              ("integrity", "f07"), ("counts", "f08"),
                              ("alerts", "f09"), ("leak", "f10")]:
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as temp:
                with self.assertRaises(AssertionError):
                    getattr(self.grader(temp, defect), check)()

    def test_untrusted_artifact_cannot_escape_store(self):
        with tempfile.TemporaryDirectory() as temp:
            grader = self.grader(temp, "artifact-escape")
            with self.assertRaisesRegex(AssertionError, "relative"):
                grader.f07()
            payload = pathlib.Path(temp) / "f07-corrupt/input/blob/binary"
            self.assertEqual(payload.read_bytes(), bytes(range(256)))

    def test_malformed_response_is_a_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            grader = self.grader(temp, "malformed")
            with self.assertRaisesRegex(AssertionError, "object"):
                grader.f01()

    def test_invalid_timestamp_does_not_pass(self):
        for value in ("2026-10-29T00:00:00", "2026-10-29T01:00:00+01:00"):
            with self.assertRaises(AssertionError):
                evaluation.stamp(value)


if __name__ == "__main__":
    unittest.main()
