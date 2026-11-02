#!/usr/bin/env python3
"""overnight-evidence.py: the stub, the scenario-to-rule match, the verdicts and the results reading. No model."""

import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "infra" / "scripts" / "overnight-evidence.py"
spec = importlib.util.spec_from_file_location("overnight_evidence", SCRIPT)
overnight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overnight)

RULE = """---
type: Rule
title: "DEL.1 Roll forward, never roll back"
description: A broken release is fixed by a new release, not by redeploying an older one.
rule_id: DEL.1
---

# Rule

Release a fix as a new deployment. One artifact or image is built once and promoted through the environments
in order; tags are versions or commit SHAs, never `latest`.
"""


class StubRule(unittest.TestCase):
    def test_keeps_frontmatter_and_replaces_the_body_with_the_description(self):
        text, cut = overnight.stub_rule(RULE)
        self.assertTrue(text.startswith(RULE.split("\n# Rule")[0]))
        self.assertIn("A broken release is fixed by a new release", text.split("---\n", 2)[2])
        self.assertNotIn("promoted through the environments", text)
        self.assertGreater(cut, 0)

    def test_a_file_without_frontmatter_is_refused(self):
        with self.assertRaises(ValueError):
            overnight.stub_rule("# Rule\n\nno frontmatter\n")


class RuleIds(unittest.TestCase):
    def test_must_find_and_must_not_find(self):
        self.assertEqual(overnight.rule_ids_of({"must_find": [{"rule_id": "T.2", "file": "src/A.cs"}]}), {"T.2"})
        self.assertEqual(overnight.rule_ids_of({"must_not_find": ["CODE.5"]}), {"CODE.5"})

    def test_an_expectation_without_rules(self):
        self.assertEqual(overnight.rule_ids_of({"max_high_findings": 0}), set())


class Verdict(unittest.TestCase):
    def test_no_scenarios_is_unmeasured(self):
        self.assertTrue(overnight.verdict([]).startswith("unmeasured"))

    def test_a_missing_result_is_incomplete(self):
        self.assertTrue(overnight.verdict([("a", "pass", None)]).startswith("incomplete"))

    def test_pass_to_fail_means_keep(self):
        self.assertTrue(overnight.verdict([("a", "pass", "pass"), ("b", "pass", "fail")]).startswith("keep"))

    def test_nothing_worse_is_a_candidate(self):
        self.assertTrue(overnight.verdict([("a", "pass", "pass"), ("b", "fail", "pass")]).startswith("cut candidate"))


class Results(unittest.TestCase):
    def test_reads_only_this_engine_and_model_and_skips_broken_lines(self):
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / "results.jsonl"
            path.write_text("\n".join([
                json.dumps({"engine": "claude", "model": "default", "scenario": "a", "status": "pass"}),
                json.dumps({"engine": "codex", "model": "default", "scenario": "b", "status": "fail"}),
                "{half a line",
            ]) + "\n", encoding="utf-8")
            self.assertEqual(overnight.statuses(path, "claude", None), {"a": "pass"})

    def test_spent_sums_measured_usage_and_keeps_unknown_apart(self):
        lines = {"a": {"usage": {"input_tokens": 100, "output_tokens": 10, "cost": 0.5}},
                 "b": {"usage": {"input_tokens": None, "cost": None}},
                 "c": {}}
        self.assertEqual(overnight.spent(lines), (110, 0.5))
        self.assertEqual(overnight.spent(lines, {"b", "c"}), (None, None))
        self.assertEqual(overnight.show(None, None), "tokens unknown")

    def test_added_lines_from_a_diff(self):
        diff = "--- a/h.jsonl\n+++ b/h.jsonl\n@@ -3,0 +4 @@\n+{\"gate\": \"pass\"}\n"
        self.assertEqual(overnight.added_lines(diff), ['{"gate": "pass"}'])


if __name__ == "__main__":
    unittest.main(verbosity=1)
