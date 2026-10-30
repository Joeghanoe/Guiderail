"""The brownfield runner is exercised with a stand-in adapter and grader; no model is involved."""
import hashlib
import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest
import unittest.mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("run_brownfield", ROOT / "harness/tools/testing/run_brownfield.py")
bf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bf)
FIXTURES = pathlib.Path(__file__).parent / "fixtures"


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(budget_seconds=None, **kwargs)


class RunBrownfieldTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = pathlib.Path(temp.name)
        source = self.root / "project" / "comp"
        (source / "Services").mkdir(parents=True)
        content = b"namespace Demo;\npublic class Thing { }\n"
        (source / "Services" / "Thing.cs").write_bytes(content)
        private = self.root / "private"
        private.mkdir()
        (private / "p.json").write_text(json.dumps({"root": str(self.root / "project"),
                                                    "components": {"comp": {"path": "comp"}}}), encoding="utf-8")
        self.cases = self.root / "cases"
        self.case = self.cases / "validation" / "v-test-01"
        self.case.mkdir(parents=True)
        (self.case / "case.json").write_text(json.dumps({"id": "v-test-01", "role": "validation", "kind": "feature",
                                                         "components": ["comp"], "rule_ids": ["CODE.5"], "hard_gates": ["T.1"]}))
        (self.case / "task.md").write_text("# Task\nAdd a class.", encoding="utf-8")
        (self.case / "criteria.md").write_text("- G01 a class is added", encoding="utf-8")
        self.pin = hashlib.sha256(content).hexdigest()
        self.write_snapshot(self.pin)
        for name, value in (("PRIVATE", private), ("CASES", self.cases)):
            patch = unittest.mock.patch.object(bf, name, value)
            patch.start()
            self.addCleanup(patch.stop)

    def write_snapshot(self, sha):
        (self.case / "snapshot.json").write_text(json.dumps({"files": [{"path": "Services/Thing.cs", "sha256": sha}]}))

    def profile(self, mode="ok", verdict="pass"):
        data = {"provider": "stub", "model": "stub-1", "adapter_version": "0", "isolation": {"mode": "none"},
                "adapter": {"argv": [sys.executable, str(FIXTURES / "fake_brownfield_adapter.py"), "--mode", mode,
                                     "--workspace", "{workspace}", "--prompt-file", "{prompt}", "--trace-dir", "{trace_dir}"]},
                "grader": {"argv": [sys.executable, str(FIXTURES / "fake_grader.py"), verdict]}}
        path = self.root / f"profile-{mode}-{verdict}.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def run_it(self, profile, name="run"):
        args = Args(case=str(self.case), profile=str(profile), out=str(self.root / name))
        with unittest.mock.patch("builtins.print"):
            code = bf.run_case(args)
        return code, json.loads((self.root / name / "report.json").read_text(encoding="utf-8"))

    def test_run_grades_the_diff_and_keeps_criteria_from_the_candidate(self):
        code, report = self.run_it(self.profile())
        self.assertEqual(report["functional"]["status"], "pass")
        self.assertEqual(report["hard_gate_violations"], [])
        self.assertEqual(report["build_and_tests"]["status"], "inconclusive")
        self.assertIn("public class Added", (self.root / "run" / "candidate.diff").read_text(encoding="utf-8"))
        self.assertFalse(list((self.root / "run" / "workspace").rglob("criteria.md")))
        self.assertIn(code, (0, 2))

    def test_failed_rubric_item_fails_the_run(self):
        code, report = self.run_it(self.profile(verdict="fail"))
        self.assertEqual((code, report["status"]), (1, "fail"))

    def test_second_type_in_an_existing_file_is_an_introduced_code5_finding(self):
        _, report = self.run_it(self.profile(mode="twotypes"))
        code5 = report["architecture"]["code5"]
        self.assertEqual((code5["status"], code5["introduced"]), ("fail", 1), code5)
        self.assertEqual(report["status"], "fail")

    def test_credential_in_the_diff_is_a_hard_gate_violation(self):
        _, report = self.run_it(self.profile(mode="secret"))
        self.assertIn("credential-pattern-in-added-code", report["hard_gate_violations"])
        self.assertEqual(report["status"], "fail")

    def test_unchanged_workspace_is_inconclusive_not_a_pass(self):
        _, report = self.run_it(self.profile(mode="noop"))
        self.assertEqual(report["status"], "inconclusive")

    def test_replay_regrades_without_rerunning_the_candidate(self):
        self.run_it(self.profile())
        args = Args(case=str(self.case), run=str(self.root / "run"), profile=str(self.profile(verdict="fail")))
        with unittest.mock.patch("builtins.print"):
            bf.regrade(args)
        report = json.loads((self.root / "run" / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["functional"]["status"], "fail")

    def test_preflight_refuses_changed_source_holdout_and_reused_output(self):
        self.write_snapshot("0" * 64)
        with self.assertRaises(bf.rc.Preflight):
            self.run_it(self.profile(), "stale")
        self.write_snapshot(self.pin)
        self.run_it(self.profile(), "again")
        with self.assertRaises(bf.rc.Preflight):
            self.run_it(self.profile(), "again")
        data = json.loads((self.case / "case.json").read_text())
        data["role"] = "holdout"
        (self.case / "case.json").write_text(json.dumps(data))
        with self.assertRaises(bf.rc.Preflight):
            self.run_it(self.profile(), "sealed")

    def test_unparseable_grader_reply_is_inconclusive(self):
        self.assertEqual(bf.parse_grade("no json")[0], None)
        self.assertEqual(bf.parse_grade('{"items":[{"id":"G01","verdict":"maybe"}],"hard_gates":[],"regressions":[]}')[0], None)


if __name__ == "__main__":
    unittest.main()
