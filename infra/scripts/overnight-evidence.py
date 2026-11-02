#!/usr/bin/env python3
"""Overnight evidence run: a clean reviewer-eval baseline, then a rule ablation (ADR 0007 decisions 1 and 5).

In order, and resumable at any point (quota, login, Ctrl-C, a sleeping laptop):
  1. Check out --ref (default origin/main) as a detached worktree outside your checkout. The run measures one clean
     commit, and nothing you edit meanwhile changes it.
  2. Baseline: every gating reviewer scenario through eval-queue.py with --append-history. The results file lives
     outside the worktree, so the worktree stays the commit it measures.
  3. Ablation: per rule in --rules, a copy of the bundle with that rule's body cut to its one-line description.
     The frontmatter, the ID and the summary stay, as `bundle.py select --brief` shows them. Only the scenarios that
     test that rule run again, and they are compared with the baseline.
  4. A report: the gate line, the history.jsonl line to commit, the measured tokens and cost, and per rule the
     scenarios, before and after, words cut, measured tokens before and after, and a verdict.

It SPENDS MODEL TOKENS. `plan` shows how many reviews a run takes and spends none.

Usage:
  overnight-evidence.py plan   [--ref origin/main] [--engine claude] [--model NAME] [--rules DEL.1,T.4]
  overnight-evidence.py run    [same options]    run, or carry on where the last run stopped
  overnight-evidence.py report [same options]    rewrite the report from what has run
  overnight-evidence.py clean  [--ref ...]       remove the worktree and everything this script wrote for that ref

Exit: 0 done, 2 usage or setup problem, 3 stopped before finishing (run the same command again to resume).

Tool contract
  Classification:  Write, local only. Writes under $GOLDEN_PATH_HOME/workspaces/overnight-<sha>/ and adds a git
                   worktree there. Never edits your checkout, never commits, never pushes.
  Caller identity: the engine CLI's own login, done by the user. On a login or quota error eval-queue stops, and so
                   does this script.
"""

import argparse
import importlib.util
import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
REPO = pathlib.Path(__file__).resolve().parents[2]
HOME = pathlib.Path(os.getenv("GOLDEN_PATH_HOME") or pathlib.Path.home() / ".golden-path-harness")
# The short generic rules and the "mostly known" ones from the 2026-10-31 rule ranking.
DEFAULT_RULES = ("DEL.1", "DEL.2", "T.4", "IAC.5", "CODE.1", "CODE.2", "CODE.3", "CODE.4", "CODE.6", "CODE.8")
REVIEW = pathlib.Path("harness/tools/review")
HISTORY = REVIEW / "history.jsonl"
FRONTMATTER = re.compile(r"\A(---\n.*?\n---\n)(.*)\Z", re.S)
DESCRIPTION = re.compile(r"^description:\s*(.+)$", re.M)
RULE_ID = re.compile(r"^rule_id:\s*(\S+)\s*$", re.M)
TOKENS_PER_WORD = 1.3   # a rough English average; the report labels it as an estimate


# Pure helpers; tests/test_overnight_evidence.py covers them.

def stub_rule(text):
    """(stubbed text, words cut). The frontmatter stays; the body becomes the rule's one-line description."""
    match = FRONTMATTER.match(text)
    if not match:
        raise ValueError("rule file has no frontmatter")
    head, body = match.groups()
    found = DESCRIPTION.search(head)
    summary = found.group(1).strip().strip('"') if found else ""
    stub = f"\n# Rule\n\n{summary}\n"
    return head + stub, max(0, len(body.split()) - len(stub.split()))


def rule_ids_of(expect):
    """Every rule ID a scenario's expectation names: must_find entries and must_not_find IDs."""
    found = set()
    if isinstance(expect, dict):
        for key, value in expect.items():
            if key == "rule_id" and isinstance(value, str):
                found.add(value)
            elif isinstance(value, (dict, list)):
                found |= rule_ids_of(value)
    elif isinstance(expect, list):
        for value in expect:
            found |= {value} if isinstance(value, str) else rule_ids_of(value)
    return found


def result_lines(path, engine, model):
    """{scenario: results line} for one engine and model from an eval-queue results file."""
    found = {}
    if path.is_file():
        for text in path.read_text(encoding="utf-8").splitlines():
            try:
                line = json.loads(text)
            except ValueError:
                continue
            if (line.get("engine"), line.get("model")) == (engine, model or "default"):
                found[line["scenario"]] = line
    return found


def statuses(path, engine, model):
    """{scenario: pass|fail} for one engine and model."""
    return {name: line["status"] for name, line in result_lines(path, engine, model).items()}


def spent(lines, names=None):
    """(tokens in+out, cost) over the named scenarios' measured usage; None where nothing was measured."""
    usages = [(line.get("usage") or {}) for name, line in lines.items() if names is None or name in names]
    known = [u for u in usages if u.get("input_tokens") is not None]
    costs = [u["cost"] for u in usages if u.get("cost") is not None]
    tokens = sum(u["input_tokens"] + (u.get("output_tokens") or 0) for u in known) if known else None
    return tokens, round(sum(costs), 4) if costs else None


def show(tokens, cost):
    return (f"{tokens:,} tok" if tokens is not None else "tokens unknown") + (f", ${cost}" if cost is not None else "")


def verdict(rows):
    """One rule's verdict from its (scenario, before, after) rows."""
    if not rows:
        return "unmeasured: no gating reviewer eval tests this rule, so cutting it is a guess"
    if any(before is None or after is None for _, before, after in rows):
        return "incomplete: run again to finish"
    if any(before == "pass" and after == "fail" for _, before, after in rows):
        return "keep: the reviewer got worse without the full rule"
    return f"cut candidate: nothing got worse on {len(rows)} scenario(s), one run each; confirm on a second night"


def added_lines(diff):
    return [line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]


# Setup.

def git(*args, cwd=REPO, check=True):
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and result.returncode:
        raise SystemExit(f"overnight: git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_rule(bundle, rule_id):
    for path in sorted((bundle / "rules").rglob("*.md")):
        match = RULE_ID.search(path.read_text(encoding="utf-8"))
        if match and match.group(1).strip('"') == rule_id:
            return path
    raise SystemExit(f"overnight: no rule with rule_id {rule_id} under {bundle / 'rules'}")


def setup(args, create=True):
    if args.ref.startswith("origin/"):
        subprocess.run(["git", "fetch", "--quiet", "origin"], cwd=REPO)   # read-only; offline just uses what is known
    sha = git("rev-parse", "--verify", f"{args.ref}^{{commit}}")
    workspace = HOME / "workspaces" / f"overnight-{sha[:12]}"
    tree = workspace / "worktree"
    if not tree.is_dir():
        if not create:
            raise SystemExit(f"overnight: nothing has run for {args.ref} ({sha[:12]}) yet")
        workspace.mkdir(parents=True, exist_ok=True)
        git("worktree", "add", "--detach", str(tree), sha)
    elif git("rev-parse", "HEAD", cwd=tree) != sha:
        raise SystemExit(f"overnight: {tree} is not at {sha[:12]}; remove it with `clean` first")
    model_key = re.sub(r"[^A-Za-z0-9._-]", "_", args.model or "default")
    out = workspace / f"{args.engine}-{model_key}"
    out.mkdir(parents=True, exist_ok=True)
    return {"sha": sha, "workspace": workspace, "tree": tree, "out": out,
            "base_results": out / "baseline-results.jsonl", "state": out / "state.json",
            "rules": [r.strip() for r in args.rules.split(",") if r.strip()]}


def gating_scenarios(tree, bundle):
    """[(name, critical, rule IDs)] for the gating scenarios, built by eval.py itself."""
    ev = load_module(tree / REVIEW / "eval.py", "overnight_eval")
    found = []
    for scenario in ev.from_cases(bundle):
        name, spec = scenario[0], scenario[1]
        if not spec.get("advisory"):
            found.append((name, bool(spec.get("critical")), rule_ids_of(spec.get("expect", {}))))
    return found


def ablated_bundle(ctx, rule_id):
    """A copy of the bundle with one rule stubbed. Same content every time, so eval-queue resumes its checklist."""
    target = ctx["workspace"] / "ablation" / rule_id / "harness"
    if not target.is_dir():
        partial = target.with_name("harness.partial")
        shutil.rmtree(partial, ignore_errors=True)
        shutil.copytree(ctx["tree"] / "harness", partial, ignore=shutil.ignore_patterns("__pycache__", "obj", "bin"))
        rule = find_rule(partial, rule_id)
        rule.write_text(stub_rule(rule.read_text(encoding="utf-8"))[0], encoding="utf-8")
        partial.rename(target)
    return target


def queue(ctx, args, *extra):
    command = [sys.executable, "-I", str(ctx["tree"] / REVIEW / "eval-queue.py"), "run",
               "--engine", args.engine, "--no-advisory", *extra]
    if args.model:
        command += ["--model", args.model]
    print("\n$ " + " ".join(shlex.quote(part) for part in command), flush=True)
    return subprocess.run(command, cwd=ctx["tree"]).returncode


def load_state(ctx):
    path = ctx["state"]
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def save_state(ctx, state):
    ctx["state"].write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def stopped(code):
    why = "the engine is unusable or a usage error" if code == 2 else "eval-queue stopped before finishing"
    print(f"\novernight: {why} (exit {code}). Fix what it printed above, then run the same command again; "
          "finished scenarios are kept.")
    return 2 if code == 2 else 3


# Commands.

def cmd_plan(args):
    ctx = setup(args)
    thresholds = json.loads((ctx["tree"] / REVIEW / "thresholds.json").read_text(encoding="utf-8"))
    scenarios = gating_scenarios(ctx["tree"], ctx["tree"] / "harness")
    repeats = lambda items: sum(thresholds["critical_repeats"] if critical else 1 for _, critical, _ in items)
    ahead = git("rev-list", "--count", f"{ctx['sha']}..HEAD")
    print(f"ref {args.ref} = {ctx['sha'][:12]}; engine {args.engine}, model {args.model or 'default'}")
    if ahead != "0":
        print(f"note: your checkout has {ahead} commit(s) that {args.ref} does not; they are not measured")
    done = statuses(ctx["base_results"], args.engine, args.model)
    print(f"\nbaseline: {len(scenarios)} gating scenarios, {repeats(scenarios)} reviews "
          f"({len(done)} already have a result)")
    total = repeats(scenarios)
    print("\nablation:")
    for rule_id in ctx["rules"]:
        tested = [s for s in scenarios if rule_id in s[2]]
        total += repeats(tested)
        print(f"  {rule_id:8} {len(tested):3} scenario(s), {repeats(tested):3} reviews"
              + ("" if tested else "  (no eval tests it: reported as unmeasured, costs nothing)"))
    print(f"\nat most {total} reviews with {args.engine}; spends nothing until you run `run`.")
    return 0


def cmd_run(args):
    ctx = setup(args)
    state = load_state(ctx)
    if "baseline" not in state:
        dirty = git("status", "--porcelain", "--untracked-files=no", cwd=ctx["tree"])
        if dirty:
            raise SystemExit(f"overnight: the worktree has changes, so it is not a clean commit:\n{dirty}")
        code = queue(ctx, args, "--append-history", "--results-file", str(ctx["base_results"]))
        if code not in (0, 1):
            return stopped(code)
        diff = git("diff", "--no-color", "-U0", "--", str(HISTORY), cwd=ctx["tree"])
        state.update(baseline="pass" if code == 0 else "fail", history_lines=added_lines(diff))
        save_state(ctx, state)
    scenarios = gating_scenarios(ctx["tree"], ctx["tree"] / "harness")
    for rule_id in ctx["rules"]:
        names = [name for name, _, ids in scenarios if rule_id in ids]
        if not names:
            continue
        results = ctx["out"] / f"ablation-{rule_id}.jsonl"
        if all(name in statuses(results, args.engine, args.model) for name in names):
            continue
        only = [part for name in names for part in ("--only", name)]
        code = queue(ctx, args, "--bundle", str(ablated_bundle(ctx, rule_id)), "--results-file", str(results), *only)
        if code not in (0, 1):
            write_report(ctx, args)
            return stopped(code)
    print(f"\ndone. report: {write_report(ctx, args)}")
    return 0


def write_report(ctx, args):
    state = load_state(ctx)
    scenarios = gating_scenarios(ctx["tree"], ctx["tree"] / "harness")
    base_lines = result_lines(ctx["base_results"], args.engine, args.model)
    before = {name: line["status"] for name, line in base_lines.items()}
    lines = [f"# Overnight evidence: {ctx['sha'][:12]} ({args.ref})", "",
             f"Engine `{args.engine}`, model `{args.model or 'default'}`. Written by `infra/scripts/overnight-evidence.py`.",
             "", "## Baseline (ADR 0007 decision 1)", ""]
    if "baseline" not in state:
        lines.append("Not finished yet: run the same command again.")
    else:
        lines.append(f"Gate: **{state['baseline']}** ({sum(s == 'pass' for s in before.values())}/{len(before)} "
                     f"gating scenarios passed). Spent: {show(*spent(base_lines))}.")
        if state.get("history_lines"):
            lines += ["", "Commit this as evidence: on a branch from `main`, append it to "
                      "`harness/tools/review/history.jsonl`.", "", "```json", *state["history_lines"], "```"]
        else:
            lines += ["", "No history.jsonl line was written; eval-queue's output above says why."]
    lines += ["", "## Rule ablation", "",
              "Each rule's body cut to its one-line description; only the scenarios that test it ran again.", "",
              "| Rule | Scenarios | Before → after (pass) | Words cut (≈ tokens per load) | Measured before → after | Verdict |",
              "|---|---|---|---|---|---|"]
    for rule_id in ctx["rules"]:
        names = [name for name, _, ids in scenarios if rule_id in ids]
        after_lines = result_lines(ctx["out"] / f"ablation-{rule_id}.jsonl", args.engine, args.model)
        after = {name: line["status"] for name, line in after_lines.items()}
        rows = [(name, before.get(name), after.get(name)) for name in names]
        cut = stub_rule(find_rule(ctx["tree"] / "harness", rule_id).read_text(encoding="utf-8"))[1]
        passed = lambda side: sum(row[side] == "pass" for row in rows)
        measured = f"{show(*spent(base_lines, names))} → {show(*spent(after_lines, names))}" if names else "—"
        lines.append(f"| {rule_id} | {len(rows)} | {passed(1)} → {passed(2)} | {cut} (≈{round(cut * TOKENS_PER_WORD)}) "
                     f"| {measured} | {verdict(rows)} |")
        lines += [f"|  | `{name}` | {b or '—'} → {a or '—'} |  |  |  |" for name, b, a in rows if b != a]
    lines += ["", "## Reading this", "",
              "- One run per scenario (critical ones get their repeats), so a single flip can be noise. A rule is",
              "  safe to cut only after a second night agrees.",
              "- Words cut are paid only when an agent opens the rule; `select --brief` already shows the summary.",
              "- Measured tokens come from each engine's own report (usage.json, ADR 0007 decision 3). Run-to-run",
              "  variation is larger than one rule's size, so read them as a sanity check, not as the saving.",
              "- Not in this script: compressing `AGENTS.base.md`, which is an edit to make and then measure here.", ""]
    report = ctx["out"] / "report.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    return report


def cmd_report(args):
    ctx = setup(args, create=False)
    print(write_report(ctx, args))
    return 0


def cmd_clean(args):
    sha = git("rev-parse", "--verify", f"{args.ref}^{{commit}}")
    workspace = HOME / "workspaces" / f"overnight-{sha[:12]}"
    if (workspace / "worktree").is_dir():
        git("worktree", "remove", "--force", str(workspace / "worktree"))
    shutil.rmtree(workspace, ignore_errors=True)
    print(f"removed {workspace}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("command", choices=["plan", "run", "report", "clean"])
    parser.add_argument("--ref", default="origin/main", help="the commit to measure (default: origin/main)")
    parser.add_argument("--engine", default="claude", choices=["claude", "codex", "copilot", "agy"])
    parser.add_argument("--model", help="model to pin; a different model is a separate run")
    parser.add_argument("--rules", default=",".join(DEFAULT_RULES), help="comma-separated rule IDs to ablate")
    args = parser.parse_args()
    return {"plan": cmd_plan, "run": cmd_run, "report": cmd_report, "clean": cmd_clean}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
