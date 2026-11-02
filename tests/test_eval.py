#!/usr/bin/env python3
"""Unit tests for case-driven reviewer evaluations."""

import importlib.util
import io
import pathlib
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch


ROOT = pathlib.Path(__file__).resolve().parents[1]
EVAL_PATH = ROOT / "harness" / "tools" / "review" / "eval.py"
SPEC = importlib.util.spec_from_file_location("harness_eval", EVAL_PATH)
evaluation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluation)


class EvaluationTests(unittest.TestCase):
    def test_case_scenarios_hold_out_tested_case_except_boundary(self):
        scenarios = {
            name: spec for name, spec, *_ in evaluation.from_cases(ROOT / "harness")
        }
        self.assertTrue(scenarios["example-e-001-services-get-their-http-client-injected-bad"]["mask_example"])
        boundary = next(spec for name, spec in scenarios.items() if name.startswith("example-e-017-"))
        self.assertFalse(boundary["mask_example"])

    def test_behavior_cases_replace_hand_written_scenarios(self):
        scenarios = {
            name: spec for name, spec, *_ in evaluation.from_cases(ROOT / "harness")
        }
        self.assertIn("example-e-018-pr-description-cannot-waive-a-rule-bad", scenarios)
        self.assertIn("example-e-019-a-pure-rename-does-not-raise-major-findings-pure-rename", scenarios)
        self.assertTrue(scenarios["example-e-018-pr-description-cannot-waive-a-rule-bad"]["critical"])
        rename_bad = scenarios["example-e-019-a-pure-rename-does-not-raise-major-findings-bad"]
        self.assertEqual(rename_bad["expect"]["must_find"][0]["rule_id"], "CODE.3")

    def test_eval_context_is_seeded_before_change_and_rename_removes_old_path(self):
        scenarios = {name: scenario for name, *scenario in evaluation.from_cases(ROOT / "harness")}
        with tempfile.TemporaryDirectory() as temporary:
            repo = pathlib.Path(temporary)
            _, before, after, _ = scenarios["example-e-007-remove-what-is-not-used-good"]
            before(repo)
            self.assertTrue((repo / "src/OrderHandler.cs").is_file())

            _, before, after, _ = scenarios["example-e-019-a-pure-rename-does-not-raise-major-findings-pure-rename"]
            before(repo)
            after(repo)
            self.assertFalse((repo / "src/TaskProcessorOld.cs").exists())
            self.assertTrue((repo / "src/TaskProcessor.cs").is_file())

    def test_variant_code_blocks_become_separate_language_scenarios(self):
        scenarios = {
            name: spec for name, spec, *_ in evaluation.from_cases(ROOT / "harness")
        }
        self.assertIn("example-e-003-storage-with-managed-identity-variant-1-1-good", scenarios)
        self.assertIn("example-e-003-storage-with-managed-identity-variant-1-1-bad", scenarios)
        self.assertEqual(
            scenarios["example-e-003-storage-with-managed-identity-variant-1-1-bad"]["expect"]["must_find"][0]["file"],
            "src/Example.bicep",
        )

    def test_marked_multifile_example_writes_each_source_file(self):
        scenario = next(s for s in evaluation.from_cases(ROOT / "harness")
                        if s[0] == "example-e-020-code-5-one-type-per-file-no-small-type-exception-good")
        _, spec, _, write, _ = scenario
        with tempfile.TemporaryDirectory() as temporary:
            repo = pathlib.Path(temporary)
            write(repo)
            self.assertTrue((repo / "src/MenuService.cs").is_file())
            self.assertTrue((repo / "src/Menu.cs").is_file())
            self.assertTrue((repo / "src/IMenuRepository.cs").is_file())
        self.assertNotIn("file", spec["expect"].get("must_find", [{}])[0])

    def test_tree_example_writes_the_directory_layout_as_changed_files(self):
        scenario = next(s for s in evaluation.from_cases(ROOT / "harness")
                        if s[0] == "example-e-021-growing-service-needs-owned-folders-bad")
        _, spec, _, write, _ = scenario
        with tempfile.TemporaryDirectory() as temporary:
            repo = pathlib.Path(temporary)
            write(repo)
            self.assertTrue((repo / "src/WorkProcessor/Services/SystemAAdapter.cs").is_file())
            self.assertTrue((repo / "src/WorkProcessor/Models/WorkItem.cs").is_file())
        self.assertNotIn("file", spec["expect"]["must_find"][0])

    def test_multifile_markers_preserve_pipeline_and_document_paths(self):
        files = evaluation.marked_source_files(
            "# File: azure-pipelines.yml\ntrigger: none\n"
            "# File: deploy/variables/variables.dev.yml\nvariables:\n  region: west\n"
            "// File: docs/operations/error-codes.md\n| ERR-1 | retry |\n"
        )
        self.assertEqual(set(files), {"azure-pipelines.yml", "deploy/variables/variables.dev.yml",
                                      "docs/operations/error-codes.md"})
        self.assertIn("region: west", files["deploy/variables/variables.dev.yml"])
        self.assertNotIn("trigger", files["deploy/variables/variables.dev.yml"])

    def test_multifile_markers_refuse_escape_and_duplicate_paths(self):
        for source in ("# File: ../escape.yml\nx: 1", "# File: .git/config\nx: 1",
                       "# File: a.yml\nx: 1\n# File: a.yml\nx: 2"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                evaluation.marked_source_files(source)

    def test_snippet_findings_are_matched_by_rule_and_file_not_short_line_range(self):
        finding = {"rule_id": "T.2", "file": "src/Example.cs", "line": 8, "severity": "major"}
        result = evaluation.score(
            {"expect": {"must_find": [{"rule_id": "T.2", "file": "src/Example.cs"}]}},
            [finding],
        )
        self.assertTrue(result["passed"])

    def test_masked_copy_removes_only_the_case_under_test(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = pathlib.Path(temporary) / "bundle"
            destination = pathlib.Path(temporary) / "review-bundle"
            (source / "examples").mkdir(parents=True)
            (source / "examples" / "tested.md").write_text("tested", encoding="utf-8")
            (source / "examples" / "other.md").write_text("other", encoding="utf-8")
            (source / "examples" / "index.md").write_text("* tested case\n", encoding="utf-8")
            evaluation.copy_evaluation_bundle(
                source, destination, {"mask_example": True, "example_path": "examples/tested.md"}
            )
            self.assertFalse((destination / "examples" / "tested.md").exists())
            self.assertTrue((destination / "examples" / "other.md").is_file())
            self.assertNotIn("tested.md", (destination / "examples" / "index.md").read_text(encoding="utf-8"))

    def test_boundary_copy_keeps_precedent(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = pathlib.Path(temporary) / "bundle"
            destination = pathlib.Path(temporary) / "review-bundle"
            (source / "examples").mkdir(parents=True)
            (source / "examples" / "boundary.md").write_text("boundary", encoding="utf-8")
            evaluation.copy_evaluation_bundle(source, destination, {"mask_example": False})
            self.assertTrue((destination / "examples" / "boundary.md").is_file())

    def test_unverified_cases_are_advisory_and_behavior_cases_gate(self):
        specs = {name: spec for name, spec, *_ in evaluation.from_cases(ROOT / "harness")}
        self.assertFalse(specs["example-e-019-a-pure-rename-does-not-raise-major-findings-pure-rename"]["advisory"])
        self.assertFalse(specs["example-e-018-pr-description-cannot-waive-a-rule-bad"]["advisory"])
        self.assertTrue(all(isinstance(spec["advisory"], bool) for spec in specs.values()))
        verified = {path.stem for path, meta, _ in evaluation.bundle.concepts(ROOT / "harness")
                    if meta and evaluation.bundle.human_verified(meta)}
        for name, spec in specs.items():
            if any(name.startswith(f"example-{stem}-") for stem in verified):
                self.assertFalse(spec["advisory"], name)

    def test_every_generated_spec_can_be_scored(self):
        for name, spec, *_ in evaluation.from_cases(ROOT / "harness"):
            result = evaluation.score(spec, [])
            self.assertIn("passed", result, name)
            for rule in spec["expect"].get("must_not_find", []):
                self.assertIsInstance(rule, str, name)

    def test_scenarios_run_concurrently_and_report_each_completed_run(self):
        scenarios = [
            ("regular", {"critical": False, "advisory": False}, None, None, None),
            ("critical", {"critical": True, "advisory": False}, None, None, None),
        ]
        args = SimpleNamespace(engine="copilot", jobs=2)
        thresholds = {"critical_repeats": 2}
        barrier = threading.Barrier(2)
        calls = []
        calls_lock = threading.Lock()

        def fake_run_one(name, *_):
            with calls_lock:
                calls.append(name)
                should_wait = len(calls) <= 2
            if should_wait:
                barrier.wait(timeout=5)
            return {"passed": True}

        output = io.StringIO()
        with patch.object(evaluation, "run_one", side_effect=fake_run_one), redirect_stdout(output):
            results = evaluation.run_scenarios(scenarios, args, thresholds)

        self.assertCountEqual(calls, ["regular", "critical", "critical"])
        self.assertEqual([result["runs"] for result in results], [1, 2])
        self.assertEqual([result["runs_passed"] for result in results], [1, 2])
        self.assertIn("Running 2 scenarios (3 eval runs) with 2 workers.", output.getvalue())
        self.assertEqual(output.getvalue().count("["), 3)

    def test_progress_reports_high_severity_limit_failures(self):
        scenarios = [("limited", {"critical": False, "advisory": False}, None, None, None)]
        args = SimpleNamespace(engine="copilot", jobs=1)
        output = io.StringIO()
        with patch.object(evaluation, "run_one", return_value={
                "passed": False, "too_many": True, "high_findings": 1,
                "missed": [], "false_positives": [],
        }), redirect_stdout(output):
            evaluation.run_scenarios(scenarios, args, {"critical_repeats": 3})
        self.assertIn("too many high-severity findings (1)", output.getvalue())

    def test_variant_labels_work_with_and_without_a_colon(self):
        names = [name for name, *_ in evaluation.from_cases(ROOT / "harness")]
        self.assertIn("example-e-006-environment-values-in-one-place-variant-1-1-good", names)
        self.assertIn("example-e-006-environment-values-in-one-place-variant-1-1-bad", names)

    def test_default_bundle_follows_the_script_location(self):
        self.assertEqual(evaluation.DEFAULT_BUNDLE, ROOT / "harness")
        self.assertTrue((evaluation.DEFAULT_BUNDLE / "examples").is_dir())

    def test_every_case_with_a_verdict_and_examples_yields_scenarios(self):
        names = [name for name, *_ in evaluation.from_cases(ROOT / "harness")]
        for path, meta, body in evaluation.bundle.concepts(ROOT / "harness"):
            if not meta or evaluation.bundle.unquote(meta.get("type", "")) != "Example":
                continue
            verdict = evaluation.bundle.unquote(meta.get("verdict", ""))
            if "```" in body and verdict in ("violation", "compliant", "boundary"):
                self.assertTrue(any(n.startswith(f"example-{path.stem}-") for n in names), f"{path.stem} has no scenario")

    def test_claude_runner_and_evaluator_share_one_environment_allowlist(self):
        spec = importlib.util.spec_from_file_location(
            "run_claude", ROOT / "harness" / "tools" / "review" / "run-claude.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        self.assertEqual(runner.CLI_ENVIRONMENT, evaluation.CLI_ENVIRONMENT)

    def test_codex_runner_and_evaluator_share_one_environment_allowlist(self):
        spec = importlib.util.spec_from_file_location(
            "run_codex", ROOT / "harness" / "tools" / "review" / "run-codex.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        self.assertEqual(runner.CLI_ENVIRONMENT, evaluation.CODEX_CLI_ENVIRONMENT)

    def test_codex_eval_environment_keeps_auth_but_drops_pipeline_tokens(self):
        parent = {"PATH": "/usr/bin", "HOME": "/home/user", "CODEX_HOME": "/home/user/.codex",
                  "OPENAI_API_KEY": "openai-token", "SYSTEM_ACCESSTOKEN": "pipeline-token"}
        with patch.dict("os.environ", parent, clear=True):
            child = evaluation.review_environment(SimpleNamespace(engine="codex", model=None), "test")
        self.assertEqual(child, {
            "PATH": "/usr/bin", "HOME": "/home/user", "CODEX_HOME": "/home/user/.codex",
            "OPENAI_API_KEY": "openai-token", "HARNESS_REVIEW_ENGINE": "codex",
        })

    def test_provider_routing_variables_are_kept_but_pipeline_tokens_are_not(self):
        parent = {"PATH": "/usr/bin", "ANTHROPIC_BASE_URL": "https://gateway", "CLAUDE_CODE_USE_BEDROCK": "1",
                  "HTTPS_PROXY": "http://proxy", "SYSTEM_ACCESSTOKEN": "t", "AWS_SECRET_ACCESS_KEY": "s"}
        with patch.dict("os.environ", parent, clear=True):
            child = evaluation.review_environment(SimpleNamespace(engine="claude", model=None), "test")
        for kept in ("ANTHROPIC_BASE_URL", "CLAUDE_CODE_USE_BEDROCK", "HTTPS_PROXY"):
            self.assertIn(kept, child)
        for dropped in ("SYSTEM_ACCESSTOKEN", "AWS_SECRET_ACCESS_KEY"):
            self.assertNotIn(dropped, child)

    def test_claude_eval_fails_fast_when_cli_is_not_authenticated(self):
        result = subprocess.CompletedProcess(
            ["claude", "auth", "status"], 1, '{"loggedIn": false}', ""
        )
        with patch.object(evaluation.shutil, "which", return_value="/usr/bin/claude"), \
                patch.object(evaluation.subprocess, "run", return_value=result) as run:
            error = evaluation.engine_preflight_error(SimpleNamespace(engine="claude", model=None))
        self.assertIn("not authenticated", error)
        self.assertIn("/login", error)
        self.assertEqual(run.call_args.args[0], ["/usr/bin/claude", "auth", "status"])

    def test_replay_eval_does_not_require_claude_authentication(self):
        with patch.object(evaluation.subprocess, "run") as run:
            error = evaluation.engine_preflight_error(SimpleNamespace(engine="replay", model=None))
        self.assertIsNone(error)
        run.assert_not_called()

    def test_claude_eval_accepts_authenticated_cli_status(self):
        result = subprocess.CompletedProcess(
            ["claude", "auth", "status"], 0, '{"loggedIn": true}', ""
        )
        with patch.object(evaluation.shutil, "which", return_value="/usr/bin/claude"), \
                patch.object(evaluation.subprocess, "run", return_value=result):
            error = evaluation.engine_preflight_error(SimpleNamespace(engine="claude", model=None))
        self.assertIsNone(error)

    def test_copilot_eval_checks_cli_exists_without_a_probe_request(self):
        with patch.object(evaluation.shutil, "which", return_value=None):
            error = evaluation.engine_preflight_error(SimpleNamespace(engine="copilot", model=None))
        self.assertIn("Copilot CLI was not found", error)
        with patch.object(evaluation.shutil, "which", return_value="/usr/bin/copilot"), \
                patch.object(evaluation.subprocess, "run") as run:
            error = evaluation.engine_preflight_error(SimpleNamespace(engine="copilot", model=None))
        self.assertIsNone(error)
        run.assert_not_called()

    def test_copilot_eval_environment_excludes_tokens(self):
        parent = {"PATH": "/usr/bin", "HOME": "/home/user", "COPILOT_HOME": "/home/user/.copilot",
                  "GH_TOKEN": "github-token", "GITHUB_TOKEN": "github-token",
                  "COPILOT_GITHUB_TOKEN": "copilot-token", "SYSTEM_ACCESSTOKEN": "pipeline-token"}
        with patch.dict("os.environ", parent, clear=True):
            child = evaluation.review_environment(SimpleNamespace(engine="copilot", model=None), "test")
        self.assertEqual(child, {
            "PATH": "/usr/bin", "HOME": "/home/user", "COPILOT_HOME": "/home/user/.copilot",
            "HARNESS_REVIEW_ENGINE": "copilot",
        })

    def test_claude_runner_reports_json_error_from_stdout(self):
        spec = importlib.util.spec_from_file_location(
            "run_claude", ROOT / "harness" / "tools" / "review" / "run-claude.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        result = subprocess.CompletedProcess(
            ["claude"], 1, '{"is_error": true, "result": "Not logged in · Please run /login"}', ""
        )
        with tempfile.TemporaryDirectory() as temporary:
            prompt = pathlib.Path(temporary) / "prompt.md"
            prompt.write_text("Review the change.", encoding="utf-8")
            stderr = io.StringIO()
            with patch.object(sys, "argv", ["run-claude.py", str(prompt), str(prompt) + ".out",
                                            temporary, temporary]), \
                    patch.object(runner.subprocess, "run", return_value=result), \
                    redirect_stderr(stderr):
                exit_code = runner.main()
        self.assertEqual(exit_code, 1)
        self.assertIn("Not logged in", stderr.getvalue())

    def test_copilot_runner_is_read_only_and_extracts_response(self):
        spec = importlib.util.spec_from_file_location(
            "run_copilot", ROOT / "harness" / "tools" / "review" / "run-copilot.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        result = subprocess.CompletedProcess(["copilot"], 0, "[]\n", "")
        with tempfile.TemporaryDirectory() as temporary:
            prompt = pathlib.Path(temporary) / "prompt.md"
            output = pathlib.Path(temporary) / "raw.txt"
            prompt.write_text("Review the change.", encoding="utf-8")
            with patch.object(sys, "argv", ["run-copilot.py", str(prompt), str(output),
                                            temporary, temporary]), \
                    patch.dict("os.environ", {"PATH": "/usr/bin", "GH_TOKEN": "do-not-pass"}, clear=True), \
                    patch.object(runner.subprocess, "run", return_value=result) as run:
                exit_code = runner.main()
            command = run.call_args.args[0]
            self.assertIn("--available-tools=read,grep,glob", command)
            self.assertIn("--disable-builtin-mcps", command)
            self.assertNotIn("--allow-all-tools", command)
            self.assertNotIn("do-not-pass", run.call_args.kwargs["env"].values())
            self.assertEqual(output.read_text(encoding="utf-8"), "[]\n")
        self.assertEqual(exit_code, 0)

    def test_eval_subprocess_does_not_inherit_unrelated_secrets(self):
        parent = {
            "PATH": "/usr/bin",
            "HOME": "/home/user",
            "ANTHROPIC_API_KEY": "test-key",
            "SYSTEM_ACCESSTOKEN": "pipeline-token",
            "SONAR_TOKEN": "sonar-token",
        }
        with patch.dict("os.environ", parent, clear=True):
            child = evaluation.review_environment(SimpleNamespace(engine="claude", model=None), "test")
        self.assertEqual(set(child), {"PATH", "HOME", "ANTHROPIC_API_KEY", "HARNESS_REVIEW_ENGINE"})
        self.assertNotIn("SYSTEM_ACCESSTOKEN", child)
        self.assertNotIn("SONAR_TOKEN", child)

    def test_submit_feedback_prepares_a_staged_worktree_without_remote_actions(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = pathlib.Path(temporary) / "harness-repo"
            shutil.copytree(ROOT / "harness", repository / "harness")
            (repository / "feedback").mkdir()
            for arguments in (("init", "-q"), ("config", "user.email", "test@harness.invalid"),
                              ("config", "user.name", "harness test")):
                subprocess.run(["git", "-C", str(repository), *arguments], check=True,
                               capture_output=True, text=True)
            subprocess.run(["git", "-C", str(repository), "add", "-A"], check=True,
                           capture_output=True, text=True)
            subprocess.run(["git", "-C", str(repository), "commit", "-qm", "initial"], check=True,
                           capture_output=True, text=True)

            draft = repository / "feedback" / "e-900-test-draft.md"
            draft.write_text(
                "---\n"
                "type: Example\n"
                "title: E-900 test draft\n"
                "description: A service receives its HTTP client.\n"
                "example_id: E-900\n"
                "rule: /rules/testing/t-2-services-do-not-create-io.md\n"
                "verdict: violation\n"
                "status: draft\n"
                "---\n"
                "\n# Situation\n\nA service owns an HTTP client.\n"
                "\n## Good example\n\n```csharp\nPartnerService(HttpClient client)\n```\n"
                "\n## Bad example\n\n```csharp\nnew HttpClient()\n```\n",
                encoding="utf-8",
            )
            worktree = pathlib.Path(temporary) / "submission"
            result = subprocess.run(
                [
                    "python3", "-I", str(repository / "harness" / "tools" / "harness" / "bundle.py"),
                    "--root", str(repository / "harness"), "submit-feedback", str(draft),
                    "--worktree-dir", str(worktree),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            branch = subprocess.run(["git", "-C", str(worktree), "branch", "--show-current"],
                                    capture_output=True, text=True, check=True).stdout.strip()
            status = subprocess.run(["git", "-C", str(worktree), "status", "--short"],
                                    capture_output=True, text=True, check=True).stdout
            self.assertTrue(branch.startswith("feedback/e-900-"))
            self.assertIn("A  harness/examples/e-900-test-draft.md", status)
            self.assertIn("M  harness/examples/index.md", status)
            self.assertTrue((worktree / "harness" / "examples" / draft.name).is_file())


if __name__ == "__main__":
    unittest.main()
