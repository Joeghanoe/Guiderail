"""Harness usage and denied-command reports read traces only; no model is involved."""
import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("harness_usage", ROOT / "harness/tools/testing/harness_usage.py")
hu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hu)


def tool(call_id, name, **args):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": call_id, "name": name, "input": args}]}}


def denied(call_id):
    return {"type": "system", "subtype": "permission_denied", "tool_use_id": call_id, "tool_name": "Bash"}


class HarnessUsageTests(unittest.TestCase):
    def make_run(self, events, name="r1"):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        run = pathlib.Path(temp.name) / name
        (run / "trace").mkdir(parents=True)
        (run / "trace" / "claude-events.jsonl").write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
        rules = run / "workspace" / ".harness" / "rules" / "code"
        rules.mkdir(parents=True)
        (rules / "code-5-one-responsibility.md").write_text("---\nrule_id: CODE.5\n---\nbody", encoding="utf-8")
        (rules / "code-1-remove.md").write_text("---\nrule_id: CODE.1\n---\nbody", encoding="utf-8")
        (run / "workspace" / ".harness" / "index.md").write_text("index", encoding="utf-8")
        return run

    def test_denied_commands_are_classified_by_cause(self):
        run = self.make_run([
            tool("a", "Bash", command="cd /work; bash scripts/verify.sh"), denied("a"),
            tool("b", "Bash", command="echo x | python3 .harness/tools/harness/bundle.py select"), denied("b"),
            tool("c", "Bash", command="python3 -I /tmp/apply.py"), denied("c"),
            tool("d", "Bash", command="cd /work; python3 - <<'E'\nprint(1)\nE"), denied("d"),
            tool("e", "Bash", command="curl example.test"), denied("e")])
        causes = {d["command"][:12]: d["cause"] for d in hu.denied_calls(run)}
        self.assertEqual(sorted(causes.values()), ["harness-documented", "harness-documented", "other", "shell-write", "shell-write"])
        self.assertTrue(next(d for d in hu.denied_calls(run) if "verify" in d["command"])["cd_prefix"])

    def test_opened_files_and_cited_rule_ids_come_from_the_agents_own_events_only(self):
        run = self.make_run([
            tool("a", "Read", file_path="/work/.harness/index.md"),
            {"type": "user", "message": {"content": [{"type": "tool_result", "content": ".harness/rules/code/code-1-remove.md"}]}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "Applied CODE.5 here."}]}}])
        base = pathlib.Path(run.parent / "AGENTS.base.md")
        base.write_text("# T\n\n## Done\n\nRun `scripts/verify.sh` and `tools/never-run.sh` (T.1).\n", encoding="utf-8")
        result = hu.analyse([run], ROOT / "harness", base)
        self.assertEqual(dict(result["opened"]), {"index.md": 1})
        self.assertEqual(dict(result["cited"]), {"rules/code/code-5-one-responsibility.md": 1})
        section = next(s for s in result["base_sections"] if s["section"] == "Done")
        self.assertEqual(section["referenced"], [])  # nothing the agent ran or said named them
        self.assertIn("Never opened: 2 of 3", hu.render(result))

    def test_diagnosis_flags_a_denial_when_nothing_changed(self):
        spec2 = importlib.util.spec_from_file_location("diagnose_run", ROOT / "harness/tools/testing/diagnose_run.py")
        dr = importlib.util.module_from_spec(spec2)
        spec2.loader.exec_module(dr)
        run = self.make_run([tool("a", "Bash", command="python3 .harness/tools/harness/bundle.py select"), denied("a")])
        (run / "report.json").write_text(json.dumps({"case_id": "c", "status": "inconclusive", "hard_gate_violations": [],
            "execution": {}, "architecture": {}, "functional": {}, "observations": {"files_changed": []}}), encoding="utf-8")
        found = {f["signal"]: f for f in dr.propose(run)["findings"]}
        finding = found["1 command(s) denied by the adapter allowlist"]
        self.assertIn("rerun", finding["why"])
        self.assertIn("propose an allowlist entry", finding["why"])


if __name__ == "__main__":
    unittest.main()
