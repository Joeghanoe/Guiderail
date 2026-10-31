#!/usr/bin/env python3
"""Diagnose disagreements in a finished run (ADR 0005 lifecycle step 5). Reads evidence only; never reruns anything.

`propose` lists each disagreement or doubtful result in report.json with a suggested class and the evidence behind it,
and writes diagnosis.json next to the report. A suggestion is a lead, not a verdict: only `record`, run by a person,
sets a class. Rules, principles, criteria and graders are never edited here (step 6 proposes those changes for review).
"""
import argparse
import json
import pathlib
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import harness_usage  # noqa: E402

CLASSES = ("project-defect", "evaluator-defect", "incomplete-principle", "model-or-harness-failure", "insufficient-evidence")
EVIDENCE_PATH = re.compile(r"([\w./-]+\.\w+)(?::(\d+))?")


def finding(number, signal, suggested, confidence, evidence, why):
    return {"id": f"D{number:02d}", "signal": signal, "suggested_class": suggested, "confidence": confidence,
            "evidence": evidence, "why": why, "classification": None, "reviewed_by": None, "note": None}


def cited_location(evidence, workspace, changed):
    """True when the grader's evidence names a changed file (and a line that exists) in the final workspace."""
    for match in EVIDENCE_PATH.finditer(str(evidence or "")):
        path, line = match.group(1), match.group(2)
        if path not in changed:
            continue
        target = workspace / path
        if not target.is_file():
            continue
        return not line or int(line) <= len(target.read_text(encoding="utf-8", errors="replace").splitlines())
    return False


def propose(run):
    report = json.loads((run / "report.json").read_text(encoding="utf-8"))
    workspace = run / "workspace"
    found = []
    add = lambda *a: found.append(finding(len(found) + 1, *a))
    execution = report.get("execution", {})
    code5 = report.get("architecture", {}).get("code5", {})
    functional = report.get("functional", {})
    observations = report.get("observations", {})
    changed = {entry.split(" ", 1)[1] for entry in observations.get("files_changed", [])}

    if execution.get("adapter_error") or execution.get("timed_out"):
        add("agent did not finish", "model-or-harness-failure", "high",
            {"adapter_error": execution.get("adapter_error"), "timed_out": execution.get("timed_out"),
             "runtime_seconds": execution.get("runtime_seconds")},
            "A timeout or adapter error says nothing about the project or the criteria; rerun before drawing conclusions.")
    elif "files_changed" in observations and not changed:
        add("candidate changed nothing", "model-or-harness-failure", "medium", {"adapter_exit_code":
            report.get("behavior", {}).get("adapter_exit_code")}, "No diff: check the trace for a refusal, a tool block or a misread task.")

    denied = harness_usage.denied_calls(run)
    if denied:
        causes = sorted({d["cause"] for d in denied})
        gap = [d for d in denied if d["cause"] in ("harness-documented", "compound")]
        add(f"{len(denied)} command(s) denied by the adapter allowlist", "model-or-harness-failure", "medium" if not changed else "low",
            {"denied": denied[:8], "causes": causes, "run_void_if_no_diff": not changed},
            ("Nothing changed after a denial: the run measures the allowlist, not the candidate; rerun after deciding. " if not changed else "")
            + ("Some denied commands are ones the harness tells agents to run, or only fail because of a `cd` prefix or a pipe: "
               "propose an allowlist entry or an instruction fix for review (step 6); this tool changes neither. " if gap else
               "The denied commands are shell file writes or unclassified; read them before blaming the allowlist."))
    grade = functional.get("grade") or {}
    if grade.get("status") == "inconclusive" or functional.get("status") == "inconclusive":
        add("grading inconclusive", "insufficient-evidence", "high", {"reason": grade.get("reason") or functional.get("reason")},
            "Nothing was decided; fix the grader command or output and replay with `grade`.")
    for item in grade.get("items", []):
        verifiable = cited_location(item.get("evidence"), workspace, changed)
        absence = re.match(r"\s*(the (diff|change) )?(adds? )?(no|not|none|missing)\b", str(item.get("evidence", "")), re.I)
        if item["verdict"] == "fail" and not verifiable and absence:
            add(f"{item['id']} failed because something is absent", "model-or-harness-failure", "low",
                {"item": item, "files_changed": sorted(changed)},
                "An absence has no line to cite; confirm against the changed-file list that it really is missing.")
        elif item["verdict"] == "fail" and not verifiable:
            add(f"{item['id']} failed without checkable evidence", "evaluator-defect", "medium", item,
                "The judge cited no changed file and line; read the diff before blaming the candidate.")
        elif item["verdict"] == "inconclusive":
            add(f"{item['id']} undecided", "insufficient-evidence", "medium", item,
                "The change or snapshot does not show enough to decide; consider whether the criterion is checkable.")
    scored = code5.get("scored", True)
    if code5.get("introduced") and any(i["verdict"] == "pass" for i in grade.get("items", [])):
        add("CODE.5 introduced findings alongside rubric passes", "evaluator-defect" if scored else "incomplete-principle",
            "medium" if scored else "low", {"code5": code5, "scored": scored},
            "Judge and checker disagree." if scored else
            "CODE.5 is not in this case's rule list, so it did not decide the verdict; decide whether the case or the rule scope is wrong.")
    if code5.get("status") == "fail" and any(i["verdict"] == "pass" for i in grade.get("items", [])) and not code5.get("introduced"):
        add("CODE.5 failed with no introduced finding", "evaluator-defect", "high", code5, "Baseline comparison looks wrong.")
    if code5.get("inherited"):
        add("snapshot already violates CODE.5", "project-defect", "high",
            {"inherited": code5["inherited"]}, "Present before the candidate; report as inherited debt, not as a regression.")

    for violation in report.get("hard_gate_violations", []):
        if violation.startswith("rubric-hard-gate:"):
            add(f"rubric hard gate {violation.split(':', 1)[1]}", "model-or-harness-failure", "low", {"violation": violation},
                "An LLM-judged hard gate needs a person's confirmation before it counts; check the diff.")
        elif violation == "credential-pattern-in-added-code":
            add("credential pattern in the diff", "evaluator-defect", "low", {"violation": violation, "files": sorted(changed)},
                "Confirm it is not a placeholder or a test string; a real credential is a model failure and a hard stop.")
        else:
            add(violation, "model-or-harness-failure", "medium", {"violation": violation},
                "Deterministic hard gate: the candidate touched something it must not.")

    classified = [f for f in found if f["suggested_class"] == "model-or-harness-failure"]
    explained = (code5.get("status") == "fail" or report.get("hard_gate_violations")
                 or any(i["verdict"] == "fail" for i in grade.get("items", [])))
    if report.get("status") == "fail" and not found and not explained:
        add("failed with no recorded cause", "insufficient-evidence", "high", {"status": report["status"]},
            "The report fails without a signal this tool recognises; read the report and trace.")
    if len(classified) >= 3:
        found[0]["note"] = "several model/harness leads in one run; the harness instructions may be unclear (not auto-classified)"
    diagnosis = {"schema_version": 1, "case_id": report.get("case_id") or report.get("scenario_id"), "run_status": report.get("status"),
                 "proposed_at": datetime.now(timezone.utc).isoformat(), "classes": CLASSES, "findings": found}
    (run / "diagnosis.json").write_text(json.dumps(diagnosis, indent=2), encoding="utf-8")
    return diagnosis


def record(run, finding_id, klass, by, note):
    path = run / "diagnosis.json"
    diagnosis = json.loads(path.read_text(encoding="utf-8"))
    if klass not in CLASSES:
        raise SystemExit("class must be one of: " + ", ".join(CLASSES))
    if not by.strip():
        raise SystemExit("--by must name the reviewer")
    for item in diagnosis["findings"]:
        if item["id"] == finding_id:
            item.update(classification=klass, reviewed_by=by, note=note)
            path.write_text(json.dumps(diagnosis, indent=2), encoding="utf-8")
            return item
    raise SystemExit("no such finding: " + finding_id)


def render(diagnosis):
    lines = [f"# Diagnosis {diagnosis['case_id']} (run {diagnosis['run_status']})", ""]
    for item in diagnosis["findings"]:
        decided = item["classification"] or f"unreviewed (suggest {item['suggested_class']}, {item['confidence']})"
        lines += [f"- {item['id']} {item['signal']}: {decided}", f"  {item['why']}"]
    open_count = sum(1 for f in diagnosis["findings"] if not f["classification"])
    lines.append(f"\n{open_count} of {len(diagnosis['findings'])} awaiting a reviewer. Classes: {', '.join(CLASSES)}.")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("propose")
    p.add_argument("--run", required=True)
    r = sub.add_parser("record")
    r.add_argument("--run", required=True)
    r.add_argument("--finding", required=True)
    r.add_argument("--class", dest="klass", required=True)
    r.add_argument("--by", required=True, help="the person who reviewed it")
    r.add_argument("--note", default="")
    args = parser.parse_args()
    run = pathlib.Path(args.run).resolve(strict=True)
    if args.command == "propose":
        print(render(propose(run)))
    else:
        record(run, args.finding, args.klass, args.by, args.note)
        print(render(json.loads((run / "diagnosis.json").read_text(encoding="utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
