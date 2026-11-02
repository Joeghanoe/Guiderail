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
                              ("alerts", "f09"), ("leak", "f10"),
                              ("status-writes", "f11"), ("health-always", "f12"), ("health-writes", "f12"),
                              ("dryrun-writes", "f13"), ("exclusion-stored", "f14"),
                              ("events-leak", "f15"), ("events-missing", "f15"), ("traversal", "f16")]:
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as temp:
                with self.assertRaises(AssertionError):
                    getattr(self.grader(temp, defect), check)()

    def test_extended_criteria_pass_the_positive_control(self):
        with tempfile.TemporaryDirectory() as temp:
            report = evaluation.Grader([sys.executable, str(CONTROL), "none"], temp,
                                       criteria=[f"F{n:02}" for n in range(1, 17)]).run()
            self.assertEqual(report["functional_status"], "pass", report["checks"])
            self.assertEqual(len(report["checks"]), 16)

    def test_hostile_identifier_acceptance_is_a_hard_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            report = evaluation.Grader([sys.executable, str(CONTROL), "traversal"], temp, criteria=["F16"]).run()
            self.assertEqual(report["hard_gate_violations"], ["F16"])

    def test_scenario_file_selects_the_criteria(self):
        with tempfile.TemporaryDirectory() as temp:
            path = pathlib.Path(temp) / "backup_eval.py"
            self.assertIsNone(evaluation.scenario_criteria(path))
            (pathlib.Path(temp) / "scenario.json").write_text('{"eval_ids": ["F01", "F11", "CODE.5"]}')
            self.assertEqual(evaluation.scenario_criteria(path), ["F01", "F11"])

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
