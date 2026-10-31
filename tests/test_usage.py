#!/usr/bin/env python3
"""Token, cost and time per review run (ADR 0007 decision 3), and the clean-commit check of the evals. No model."""

import datetime
import importlib.util
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[1]
REVIEW = ROOT / "harness" / "tools" / "review"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


usage = load("review_usage", REVIEW / "usage.py")


class Engines(unittest.TestCase):
    def test_claude_input_includes_cache_and_cost_is_reported(self):
        found = usage.from_claude({"total_cost_usd": 0.12, "usage": {
            "input_tokens": 10, "cache_creation_input_tokens": 200, "cache_read_input_tokens": 3000, "output_tokens": 50}})
        self.assertEqual((found["input_tokens"], found["cached_input_tokens"], found["output_tokens"], found["cost"]),
                         (3210, 3000, 50, 0.12))

    def test_claude_without_usage_is_null_not_zero(self):
        found = usage.from_claude({})
        self.assertIsNone(found["input_tokens"])
        self.assertIsNone(found["cost"])

    def test_codex_sums_turns_and_counts_reasoning_as_output(self):
        stdout = "\n".join([
            json.dumps({"type": "thread.started"}),
            json.dumps({"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 40,
                                                            "output_tokens": 10, "reasoning_output_tokens": 5}}),
            "not json",
            json.dumps({"type": "turn.completed", "usage": {"input_tokens": 50, "output_tokens": 2}}),
        ])
        found = usage.from_codex(stdout)
        self.assertEqual((found["input_tokens"], found["cached_input_tokens"], found["output_tokens"]), (150, 40, 17))
        self.assertNotIn("cost", found)

    def test_codex_without_events_reports_nothing(self):
        self.assertEqual(usage.from_codex("plain text"), {"cost_reason": "Codex reported no usage"})

    def test_agy_extracts_usage_and_sums_thinking(self):
        payload = {"status": "SUCCESS", "usage": {
            "input_tokens": 100, "cache_read_tokens": 30, "output_tokens": 15, "thinking_tokens": 5}}
        found = usage.from_agy(payload)
        self.assertEqual((found["input_tokens"], found["cached_input_tokens"], found["output_tokens"]),
                         (100, 30, 20))

    def test_agy_without_usage_reports_no_usage(self):
        self.assertEqual(usage.from_agy({}), {"cost_reason": "agy reported no usage"})

    def test_usage_file_prefers_a_total_over_per_model_entries(self):
        document = {"totals": {"inputTokens": 900, "outputTokens": 90},
                    "models": [{"name": "a", "inputTokens": 600, "outputTokens": 60},
                               {"name": "b", "inputTokens": 300, "outputTokens": 30}],
                    "premiumRequests": 1}
        found = usage.from_usage_file(document)
        self.assertEqual((found["input_tokens"], found["output_tokens"], found["premium_requests"]), (900, 90, 1))

    def test_usage_file_sums_per_model_entries_without_a_total(self):
        found = usage.from_usage_file({"models": [{"input_tokens": 6, "output_tokens": 1},
                                                  {"input_tokens": 4, "output_tokens": 2}]})
        self.assertEqual((found["input_tokens"], found["output_tokens"]), (10, 3))

    def test_an_unknown_usage_file_shape_stays_null(self):
        found = usage.from_usage_file({"something": "else"})
        self.assertIsNone(found["input_tokens"])
        self.assertIn("no token counts", found["cost_reason"])


class Prices(unittest.TestCase):
    def table(self, folder, checked="2026-10-01"):
        path = pathlib.Path(folder) / "prices.json"
        path.write_text(json.dumps({"checked": checked, "models": {"m-1": {
            "input_per_mtok": 2.0, "cached_input_per_mtok": 0.5, "output_per_mtok": 10.0}}}), encoding="utf-8")
        return path

    def test_cached_input_is_priced_at_the_cached_rate(self):
        with tempfile.TemporaryDirectory() as folder:
            cost, reason = usage.price("m-1", 1_000_000, 500_000, 100_000, self.table(folder),
                                       today=datetime.date(2026, 10, 31))
        self.assertAlmostEqual(cost, 0.5 * 2.0 + 0.5 * 0.5 + 0.1 * 10.0)
        self.assertIn("2026-10-01", reason)
        self.assertNotIn("stale", reason)

    def test_an_old_price_is_used_and_called_stale(self):
        with tempfile.TemporaryDirectory() as folder:
            _, reason = usage.price("m-1", 10, 0, 1, self.table(folder, "2026-01-01"), today=datetime.date(2026, 10, 31))
        self.assertIn("stale", reason)

    def test_no_price_without_a_pinned_model_or_a_table_entry(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.table(folder)
            self.assertEqual(usage.price("default", 10, 0, 1, path)[0], None)
            self.assertEqual(usage.price("other", 10, 0, 1, path)[0], None)
            self.assertEqual(usage.price("m-1", None, None, None, path)[0], None)
            self.assertEqual(usage.price("m-1", 10, 0, 1, pathlib.Path(folder) / "missing.json")[0], None)

    def test_a_reported_cost_is_kept_and_a_missing_one_is_estimated(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict("os.environ", {"HARNESS_PRICES": str(self.table(folder))}):
            reported = usage.record("claude", "m-1", 1.0, 10, 0, 1, cost=0.9, cost_reason="reported")
            estimated = usage.record("codex", "m-1", 1.0, 1_000_000, 0, 0, cost_reason="Codex reports tokens, not cost")
        self.assertEqual((reported["cost"], reported["cost_reason"]), (0.9, "reported"))
        self.assertAlmostEqual(estimated["cost"], 2.0)
        self.assertIn("estimated", estimated["cost_reason"])


class Totals(unittest.TestCase):
    def test_unknown_stays_null_and_the_counts_say_how_many_runs_reported(self):
        summary = usage.total([{"input_tokens": 10, "output_tokens": 2, "cost": None, "wall_seconds": 3.0},
                               None,
                               {"input_tokens": 5, "output_tokens": 1, "cost": 0.01, "wall_seconds": 2.0}])
        self.assertEqual((summary["runs"], summary["runs_with_tokens"], summary["runs_with_cost"]), (3, 2, 1))
        self.assertEqual((summary["input_tokens"], summary["output_tokens"], summary["cost"]), (15, 3, 0.01))
        self.assertIsNone(summary["cached_input_tokens"])

    def test_totals_of_totals_keep_their_run_counts(self):
        first = usage.total([{"input_tokens": 1}, {"input_tokens": 2}])
        second = usage.total([None])
        summary = usage.total([first, second])
        self.assertEqual((summary["runs"], summary["runs_with_tokens"], summary["input_tokens"]), (3, 2, 3))

    def test_nothing_measured_is_all_null(self):
        summary = usage.total([None, None])
        self.assertEqual(summary["runs"], 2)
        self.assertIsNone(summary["input_tokens"])
        self.assertIn("tokens unknown", usage.describe(summary))


class Adapters(unittest.TestCase):
    def run_adapter(self, script, result, *, env=None):
        runner = load(script.replace("-", "_"), REVIEW / script)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        folder = pathlib.Path(temporary.name)
        prompt, output = folder / "prompt.md", folder / "raw.txt"
        prompt.write_text("Review the change.", encoding="utf-8")
        with patch.object(sys, "argv", [script, str(prompt), str(output), str(folder), str(folder)]), \
                patch.dict("os.environ", env or {"PATH": "/usr/bin", "HOME": str(folder)}, clear=True), \
                patch.object(runner.subprocess, "run", return_value=result) as run, redirect_stderr(io.StringIO()) as err:
            code = runner.main()
        return code, json.loads((folder / "usage.json").read_text(encoding="utf-8")), run, err.getvalue(), folder

    def test_claude_runner_writes_usage_on_success(self):
        payload = {"result": "[]", "total_cost_usd": 0.02, "usage": {"input_tokens": 5, "cache_read_input_tokens": 95,
                                                                      "output_tokens": 7}}
        code, spent, *_ = self.run_adapter("run-claude.py", subprocess.CompletedProcess(["claude"], 0, json.dumps(payload), ""))
        self.assertEqual(code, 0)
        self.assertEqual((spent["engine"], spent["input_tokens"], spent["output_tokens"], spent["cost"]),
                         ("claude", 100, 7, 0.02))
        self.assertIsNotNone(spent["wall_seconds"])

    def test_claude_runner_writes_usage_on_failure_too(self):
        payload = {"is_error": True, "result": "usage limit reached", "usage": {"input_tokens": 3, "output_tokens": 0}}
        code, spent, _, err, _ = self.run_adapter("run-claude.py",
                                                  subprocess.CompletedProcess(["claude"], 1, json.dumps(payload), ""))
        self.assertEqual(code, 1)
        self.assertEqual(spent["input_tokens"], 3)
        self.assertIn("usage limit reached", err)

    def test_codex_runner_asks_for_json_events_and_reads_their_usage(self):
        events = json.dumps({"type": "turn.completed", "usage": {"input_tokens": 70, "output_tokens": 3}})
        def run(command, **_):
            pathlib.Path(command[command.index("--output-last-message") + 1]).write_text("[]", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, events, "")
        runner = load("run_codex", REVIEW / "run-codex.py")
        with tempfile.TemporaryDirectory() as temporary:
            folder = pathlib.Path(temporary)
            (folder / "prompt.md").write_text("Review.", encoding="utf-8")
            with patch.object(sys, "argv", ["run-codex.py", str(folder / "prompt.md"), str(folder / "raw.txt"),
                                            str(folder), str(folder)]), \
                    patch.dict("os.environ", {"PATH": "/usr/bin", "HOME": temporary}, clear=True), \
                    patch.object(runner.subprocess, "run", side_effect=run) as called:
                self.assertEqual(runner.main(), 0)
            self.assertIn("--json", called.call_args.args[0])
            spent = json.loads((folder / "usage.json").read_text(encoding="utf-8"))
        self.assertEqual((spent["input_tokens"], spent["output_tokens"], spent["cost"]), (70, 3, None))

    def test_codex_runner_shows_the_error_event_text(self):
        events = json.dumps({"type": "error", "message": "You've hit your usage limit."})
        code, _, _, err, _ = self.run_adapter("run-codex.py", subprocess.CompletedProcess(["codex"], 1, events, ""))
        self.assertEqual(code, 1)
        self.assertIn("usage limit", err)

    def test_copilot_runner_asks_for_a_usage_file_in_the_review_folder(self):
        code, spent, run, _, folder = self.run_adapter("run-copilot.py",
                                                       subprocess.CompletedProcess(["copilot"], 0, "[]\n", ""))
        command = run.call_args.args[0]
        self.assertEqual(code, 0)
        self.assertEqual(command[command.index("--usage-output-file") + 1], str(folder / "copilot-usage.json"))
        self.assertIn("no usage file", spent["cost_reason"])


class CleanCommit(unittest.TestCase):
    """The evals' own record files do not make the harness dirty; the 2026-10-29 history line was lost to this."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = pathlib.Path(temporary.name)
        (self.repo / "harness/tools/review").mkdir(parents=True)
        for name in ("eval-results.jsonl", "history.jsonl", "eval.py"):
            (self.repo / "harness/tools/review" / name).write_text("x\n", encoding="utf-8")
        for args in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base"]):
            subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True)
        self.evaluation = load("harness_eval_for_usage", REVIEW / "eval.py")

    def change(self, name):
        (self.repo / "harness/tools/review" / name).write_text("changed\n", encoding="utf-8")

    def test_changed_results_and_history_are_still_clean(self):
        self.change("eval-results.jsonl")
        self.change("history.jsonl")
        (self.repo / "untracked.txt").write_text("x", encoding="utf-8")
        commit, dirty = self.evaluation.harness_commit(self.repo / "harness")
        self.assertFalse(dirty)
        self.assertTrue(commit)

    def test_any_other_tracked_change_is_dirty(self):
        self.change("eval-results.jsonl")
        self.change("eval.py")
        self.assertTrue(self.evaluation.harness_commit(self.repo / "harness")[1])


if __name__ == "__main__":
    unittest.main(verbosity=1)
