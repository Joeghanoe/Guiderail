"""Diagnosis proposes leads from run evidence and only a named reviewer can classify; no model is involved."""
import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("diagnose_run", ROOT / "harness/tools/testing/diagnose_run.py")
dr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dr)


class DiagnoseRunTests(unittest.TestCase):
    def run_dir(self, **overrides):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        run = pathlib.Path(temp.name)
        (run / "workspace" / "Services").mkdir(parents=True)
        (run / "workspace" / "Services" / "Added.cs").write_text("a\nb\nc\n", encoding="utf-8")
        report = {"case_id": "v-test-01", "status": "fail", "hard_gate_violations": [],
                  "execution": {"adapter_error": None, "timed_out": False},
                  "architecture": {"code5": {"status": "pass", "introduced": 0, "inherited": 0}},
                  "functional": {"status": "pass", "grade": {"status": "graded", "items": [
                      {"id": "G01", "verdict": "pass", "evidence": "Services/Added.cs:2"}]}},
                  "observations": {"files_changed": ["A Services/Added.cs"]}}
        report.update(overrides)
        (run / "report.json").write_text(json.dumps(report), encoding="utf-8")
        return run

    def signals(self, run):
        return {f["signal"]: f for f in dr.propose(run)["findings"]}

    def test_clean_pass_has_nothing_to_diagnose(self):
        self.assertEqual(dr.propose(self.run_dir(status="pass"))["findings"], [])

    def test_timeout_is_a_model_or_harness_lead(self):
        found = self.signals(self.run_dir(execution={"adapter_error": None, "timed_out": True, "runtime_seconds": 9}))
        self.assertEqual(found["agent did not finish"]["suggested_class"], "model-or-harness-failure")

    def test_fail_without_checkable_evidence_points_at_the_evaluator(self):
        grade = {"status": "graded", "items": [{"id": "G01", "verdict": "fail", "evidence": "somewhere in the code"}]}
        found = self.signals(self.run_dir(functional={"status": "fail", "grade": grade}))
        self.assertEqual(found["G01 failed without checkable evidence"]["suggested_class"], "evaluator-defect")

    def test_fail_citing_a_real_line_is_not_blamed_on_the_evaluator(self):
        grade = {"status": "graded", "items": [{"id": "G01", "verdict": "fail", "evidence": "Services/Added.cs:3"}]}
        self.assertEqual(self.signals(self.run_dir(functional={"status": "fail", "grade": grade})), {})

    def test_cited_line_beyond_the_file_is_not_checkable(self):
        grade = {"status": "graded", "items": [{"id": "G01", "verdict": "fail", "evidence": "Services/Added.cs:99"}]}
        self.assertIn("G01 failed without checkable evidence", self.signals(self.run_dir(functional={"status": "fail", "grade": grade})))

    def test_judge_pass_against_introduced_code5_finding_is_flagged(self):
        found = self.signals(self.run_dir(architecture={"code5": {"status": "fail", "introduced": 2, "inherited": 0}}))
        self.assertIn("G01 passed while CODE.5 found introduced violations", found)

    def test_inherited_findings_are_project_debt(self):
        found = self.signals(self.run_dir(architecture={"code5": {"status": "pass", "introduced": 0, "inherited": 4}}))
        self.assertEqual(found["snapshot already violates CODE.5"]["suggested_class"], "project-defect")

    def test_only_a_named_reviewer_sets_a_class_from_the_known_set(self):
        run = self.run_dir(hard_gate_violations=["credential-pattern-in-added-code"])
        dr.propose(run)
        with self.assertRaises(SystemExit):
            dr.record(run, "D01", "wrong", "someone", "")
        with self.assertRaises(SystemExit):
            dr.record(run, "D01", "evaluator-defect", " ", "")
        item = dr.record(run, "D01", "evaluator-defect", "reviewer", "placeholder in a test")
        self.assertEqual((item["classification"], item["reviewed_by"]), ("evaluator-defect", "reviewer"))
        self.assertIn("0 of 1 awaiting", dr.render(json.loads((run / "diagnosis.json").read_text())))


if __name__ == "__main__":
    unittest.main()
