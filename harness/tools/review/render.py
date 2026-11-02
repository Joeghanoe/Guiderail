#!/usr/bin/env python3
"""Render review findings (the JSON array bundle.py findings prints) as a readable Markdown summary.

Usage: render.py <findings.json> [--branch NAME] [--rules N] [--verified TEXT]

A finding may carry `outcome` (fixed, skipped, no_change_needed) and `reason`; the playbook adds them after it
applies fixes. The summary is for the human who reviews the end result, so it leads with the counts.
"""
import argparse
import json
import pathlib
import sys

ORDER = ["blocker", "major", "minor", "nit"]


def outcome_label(f):
    outcome = f.get("outcome")
    if outcome == "fixed":
        return "fixed"
    if outcome == "no_change_needed":
        return "no change needed"
    if outcome == "skipped":
        return "open"
    return "open"


def where(f):
    return f"{pathlib.PurePosixPath(f['file']).name}:{f['line']}"


def render(findings, branch, rules, verified):
    findings = sorted(findings, key=lambda f: (ORDER.index(f.get("severity", "major")), f["file"], f["line"]))
    fixed = sum(1 for f in findings if f.get("outcome") == "fixed")
    open_ = sum(1 for f in findings if f.get("outcome") not in ("fixed", "no_change_needed"))
    out = [
        f"Reviewed {branch} against {rules} rules. {len(findings)} findings: {fixed} fixed, {open_} open. "
        f"Verified: {verified}.",
        "",
    ]
    if not findings:
        return "\n".join(out)
    out += ["| # | Rule | Where | Severity | Confidence | Outcome |", "|---|---|---|---|---|---|"]
    for i, f in enumerate(findings, 1):
        out.append(f"| {i} | {f['rule_id']} | {where(f)} | {f.get('severity', 'major')} | {f['confidence']} | "
                   f"{outcome_label(f)} |")
    for i, f in enumerate(findings, 1):
        out += ["", f"### {i}. {f.get('summary', f['rule_id'])} ({f['rule_id']}, {outcome_label(f)})",
                f"`{f['file']}:{f['line']}`", f"Evidence: `{f['evidence']}`"]
        if f.get("outcome") == "fixed":
            out.append(f"What changed: {f.get('fix', '')}")
        else:
            if f.get("fix"):
                out.append(f"Suggested fix: {f['fix']}")
            if f.get("reason"):
                out.append(f"Why not fixed: {f['reason']}")
        if f.get("not_verified"):
            out.append(f"Not verified: {f['not_verified']}")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--branch", default="the change")
    parser.add_argument("--rules", type=int, default=0)
    parser.add_argument("--verified", default="nothing ran")
    args = parser.parse_args()
    try:
        findings = json.loads(pathlib.Path(args.file).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"render: cannot read findings ({e})", file=sys.stderr)
        return 1
    print(render(findings, args.branch, args.rules, args.verified))
    return 0


if __name__ == "__main__":
    sys.exit(main())
