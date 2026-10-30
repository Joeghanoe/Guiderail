"""The runner is exercised with a stand-in adapter and the grader control; no model is involved."""
import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest
import unittest.mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("run_candidate", ROOT / "harness/tools/testing/run_candidate.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
FIXTURES = pathlib.Path(__file__).parent / "fixtures"


class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(budget_seconds=None, **kwargs)


class RunCandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        sources = self.root / "src"
        sources.mkdir()
        (sources / "TASK.md").write_text("task", encoding="utf-8")
        (sources / "scenario.json").write_text(json.dumps(
            {"id": "t-001", "role": "calibration", "holdout": False, "budgets": {"max_duration_minutes": 1}}), encoding="utf-8")
        files = [{"source": str(sources / "TASK.md"), "path": "candidate/TASK.md"},
                 {"source": str(sources / "scenario.json"), "path": "evaluator/scenario.json"},
                 {"source": str(ROOT / "harness/tools/testing/backup_eval.py"), "path": "evaluator/backup_eval.py"}]
        self.frozen = self.root / "frozen"
        runner.freezer.freeze({"approval": "test", "harness_commit": "test", "files": files}, self.frozen)
        self.manifest_sha = runner.freezer.sha(self.frozen / "freeze.json")

    def profile(self, mode="ok", **extra):
        argv = [sys.executable, str(FIXTURES / "fake_adapter.py"), "--mode", mode, "--control", str(FIXTURES / "backup_control.py"),
                "--python", sys.executable, "--workspace", "{workspace}", "--prompt-file", "{prompt}", "--trace-dir", "{trace_dir}"]
        argv += extra.pop("adapter_extra", [])
        data = {"scenario_id": "t-001", "provider": "stub", "model": "stub-1", "adapter_version": "0", "adapter": {"argv": argv},
                "isolation": {"mode": "none"}, **extra}
        path = self.root / f"profile-{mode}.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def run_it(self, profile, name, budget=None):
        args = Args(frozen=str(self.frozen), manifest_sha256=self.manifest_sha, profile=str(profile),
                    out=str(self.root / name))
        args.budget_seconds = budget
        with unittest.mock.patch("builtins.print"):
            code = runner.run_candidate(args)
        return code, json.loads((self.root / name / "report.json").read_text(encoding="utf-8"))

    def test_complete_run_reports_separate_dimensions_without_automatic_pass(self):
        code, report = self.run_it(self.profile(), "ok")
        self.assertEqual(report["functional"]["status"], "pass", report["functional"])
        self.assertEqual(report["status"], "inconclusive")
        self.assertEqual(code, 2)
        self.assertEqual(report["run_class"], "exploratory")
        self.assertEqual(report["policy"]["status"], "inconclusive")
        self.assertEqual(report["usage"]["input_tokens"], 10)
        self.assertIsNone(report["usage"]["cost"])
        self.assertTrue(report["behavior"]["observations"]["completion_report_present"])
        self.assertIn("backup_control.py", (self.root / "ok" / "candidate.diff").read_text(encoding="utf-8"))
        self.assertEqual(report["architecture"]["code5"]["status"], "inconclusive")

    def test_time_budget_terminates_the_agent(self):
        code, report = self.run_it(self.profile("sleep"), "slow", budget=1)
        self.assertTrue(report["execution"]["timed_out"])
        self.assertLess(report["execution"]["runtime_seconds"], 30)
        self.assertEqual(report["functional"]["status"], "fail")
        self.assertEqual(code, 1)

    def test_missing_entrypoint_fails_functionally(self):
        code, report = self.run_it(self.profile("no-entrypoint"), "none")
        self.assertEqual(report["functional"]["status"], "fail")
        self.assertIn("EVAL.json", report["functional"]["reason"])

    def test_protected_path_change_is_a_hard_gate(self):
        protected = self.root / "protected.txt"
        protected.write_text("original", encoding="utf-8")
        profile = self.profile(protected_paths=[str(protected)], adapter_extra=["--touch", str(protected)])
        code, report = self.run_it(profile, "touch")
        self.assertEqual(code, 1)
        self.assertIn("protected-path-modified:" + str(protected), report["hard_gate_violations"])
        self.assertEqual(report["policy"]["status"], "fail")

    def test_preflight_rejects_unselected_model_and_tampered_package(self):
        data = json.loads(self.profile().read_text(encoding="utf-8"))
        data["model"] = None
        bad = self.root / "bad.json"
        bad.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(runner.Preflight):
            runner.load_profile(bad)
        (self.frozen / "evaluator" / "backup_eval.py").write_text("# edited", encoding="utf-8")
        with self.assertRaises(runner.Preflight):
            self.run_it(self.profile(), "tampered")

    def test_design_order_is_read_from_the_claude_trace(self):
        def trace(*paths):
            events = [{"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Write", "input": {"file_path": p}}]}} for p in paths]
            folder = self.root / ("trace-" + str(len(list(self.root.glob("trace-*")))))
            folder.mkdir()
            (folder / "claude-events.jsonl").write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
            return folder
        self.assertTrue(runner.design_before_code(trace("/work/docs/solution-design.md", "/work/src/App/A.cs")))
        self.assertFalse(runner.design_before_code(trace("/work/src/App/A.cs", "/work/docs/solution-design.md")))
        self.assertIsNone(runner.design_before_code(trace("/work/src/App/A.cs")))
        self.assertIsNone(runner.design_before_code(self.root))

    def test_code5_checker_runs_on_workspace_sources(self):
        workspace = self.root / "ws"
        workspace.mkdir()
        (workspace / "One.cs").write_text("namespace N; public class One { }", encoding="utf-8")
        (workspace / "Two.cs").write_text("namespace N; public class A { } public class B { }", encoding="utf-8")
        logs = self.root / "code5-logs"
        logs.mkdir()
        result = runner.check_code5(workspace, self.root, logs)
        self.assertEqual(result["status"], "fail", result)
        self.assertGreaterEqual(result["findings"], 1)
        (workspace / "Two.cs").unlink()
        self.assertEqual(runner.check_code5(workspace, self.root, logs)["status"], "pass")

    def test_trace_mentioning_a_protected_path_is_a_hard_gate(self):
        protected = self.root / "reference"
        protected.mkdir()
        out = self.root / "evidence"
        (out / "trace").mkdir(parents=True)
        (out / "candidate.diff").write_text("", encoding="utf-8")
        escaped = json.dumps(str(protected / "secret.cs"))
        (out / "trace" / "events.jsonl").write_text('{"path": ' + escaped + '}', encoding="utf-8")
        self.assertEqual(runner.referenced([str(protected), str(self.root / "other")], out), [str(protected)])

    def test_freeze_expands_trees_applies_replacements_and_excludes(self):
        tree = pathlib.Path(runner.REPOSITORY) / "harness"
        files = [e["path"] for e in runner.expand_tree({"source": "harness", "path": "c/.harness", "exclude": ["examples", "tools/testing", "tools/index.md"]})]
        self.assertTrue(any(f.startswith("c/.harness/rules/") for f in files))
        self.assertFalse(any("/.harness/examples/" in f or "/tools/testing/" in f or f.endswith("tools/index.md") or "__pycache__" in f for f in files))
        self.assertTrue(tree.is_dir())

    def test_folder_mode_passes_env_and_reports_same_user_class(self):
        code, report = self.run_it(self.profile(isolation={"mode": "folder"}, env={"EVAL_PROBE": "hello", "HOME": "/x/home", "SECRET": "s"}), "folder")
        self.assertEqual((self.root / "folder/trace/env.txt").read_text(encoding="utf-8"), "hello")
        self.assertEqual(report["run_class"], "exploratory-same-user")
        self.assertEqual(report["policy"]["agent_env"], {"EVAL_PROBE": "<set>", "HOME": "/x/home", "SECRET": "<set>"})
        self.assertEqual(report["policy"]["status"], "inconclusive")

    def test_credential_paths_are_watched_in_folder_mode(self):
        self.assertTrue(any(p.endswith(".ssh") for p in runner.sensitive_paths()))

    def container_profile(self, mode="ok", **extra):
        argv = ["python3", str(FIXTURES / "fake_adapter.py"), "--mode", mode, "--control", str(FIXTURES / "backup_control.py"),
                "--python", "python3", "--workspace", "{workspace}", "--prompt-file", "{prompt}", "--trace-dir", "{trace_dir}"]
        data = {"scenario_id": "t-001", "provider": "stub", "model": "stub-1", "adapter_version": "0", "adapter": {"argv": argv},
                "isolation": {"mode": "container"},
                "container": {"image": "harness-eval:test", "home_volume": "vol", "docker": [sys.executable, str(FIXTURES / "fake_docker.py")]},
                **extra}
        path = self.root / f"container-{mode}.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def docker_calls(self):
        return [json.loads(line) for line in self.docker_log.read_text(encoding="utf-8").splitlines()]

    def run_in_container(self, mode, name, **kwargs):
        self.docker_log = self.root / "docker.log"
        with unittest.mock.patch.dict("os.environ", {"FAKE_DOCKER_LOG": str(self.docker_log)}):
            return self.run_it(self.container_profile(mode, **kwargs), name, budget=kwargs.pop("budget", None))

    def test_container_run_mounts_only_what_each_phase_needs(self):
        code, report = self.run_in_container("ok", "boxed")
        self.assertEqual(report["run_class"], "isolated-container")
        self.assertEqual(report["functional"]["status"], "pass", report["functional"])
        calls = {c["name"].rsplit("-", 1)[-1]: c for c in self.docker_calls()}
        self.assertEqual({"agent", "grade", "code5"} & set(calls), {"agent", "grade"})
        out = self.root / "boxed"
        sources = lambda c: {pathlib.Path(m[0]).name if m[0] != "vol" else "vol" for m in c["mounts"]}
        self.assertEqual(sources(calls["agent"]), {"workspace", "trace", "adapters", "vol"})
        self.assertEqual(sources(calls["grade"]), {"workspace", "frozen", "grade"})
        self.assertEqual(calls["grade"]["network"], "none")
        for call in calls.values():
            self.assertIn("--cap-drop", call["flags"])
            self.assertIn("--security-opt", call["flags"])
            self.assertTrue(all(pathlib.Path(m[0]).resolve() != pathlib.Path.home() for m in call["mounts"]))
        frozen_mount = next(m for m in calls["grade"]["mounts"] if m[1] == "/frozen")
        self.assertEqual(frozen_mount[2], "ro")
        self.assertEqual(report["policy"]["container"]["image"], "harness-eval:test")
        self.assertTrue((out / "grade/grader/report.json").is_file())

    def test_container_timeout_kills_the_container(self):
        self.docker_log = self.root / "docker.log"
        with unittest.mock.patch.dict("os.environ", {"FAKE_DOCKER_LOG": str(self.docker_log)}):
            code, report = self.run_it(self.container_profile("sleep"), "boxed-slow", budget=1)
        self.assertTrue(report["execution"]["timed_out"])
        self.assertTrue(any("kill" in c for c in self.docker_calls()))

    def test_missing_image_fails_preflight(self):
        self.docker_log = self.root / "docker.log"
        with unittest.mock.patch.dict("os.environ", {"FAKE_DOCKER_LOG": str(self.docker_log), "FAKE_DOCKER_NO_IMAGE": "1"}):
            with self.assertRaises(runner.Preflight):
                self.run_it(self.container_profile(), "boxed-none")

    def test_rescore_reevaluates_without_the_agent_and_keeps_original_evidence(self):
        code, original = self.run_it(self.profile(), "first")
        run = self.root / "first"
        before = (run / "report.json").read_text(encoding="utf-8")
        args = Args(run=str(run), frozen=str(self.frozen), manifest_sha256=self.manifest_sha, profile=str(self.profile()))
        with unittest.mock.patch("builtins.print"):
            runner.rescore(args)
        self.assertEqual((run / "report.json").read_text(encoding="utf-8"), before)
        rescored = next(run.glob("rescore-*"))
        report = json.loads((rescored / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["rescore"]["previous_status"], original["status"])
        self.assertEqual(report["functional"]["status"], "pass")
        self.assertEqual(report["execution"], original["execution"])
        self.assertEqual(report["usage"], original["usage"])
        self.assertFalse((rescored / "trace").exists())

    def test_rescore_keeps_agent_phase_violations(self):
        protected = self.root / "protected2.txt"
        protected.write_text("original", encoding="utf-8")
        self.run_it(self.profile(protected_paths=[str(protected)], adapter_extra=["--touch", str(protected)]), "touched")
        run = self.root / "touched"
        args = Args(run=str(run), frozen=str(self.frozen), manifest_sha256=self.manifest_sha, profile=str(self.profile()))
        with unittest.mock.patch("builtins.print"):
            self.assertEqual(runner.rescore(args), 1)
        report = json.loads(next(run.glob("rescore-*")).joinpath("report.json").read_text(encoding="utf-8"))
        self.assertIn("protected-path-modified:" + str(protected), report["hard_gate_violations"])

    def test_output_inside_the_repository_is_refused(self):
        args = Args(frozen=str(self.frozen), manifest_sha256=self.manifest_sha, profile=str(self.profile()),
                    out=str(ROOT / "run-evidence"))
        with self.assertRaises(runner.Preflight):
            runner.run_candidate(args)


if __name__ == "__main__":
    import unittest.mock
    unittest.main()
