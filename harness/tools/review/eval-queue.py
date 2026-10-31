#!/usr/bin/env python3
"""Run the reviewer evals one scenario at a time and check each off, so a run that stops can be resumed.

`eval.py` runs everything or nothing: if the model budget runs out halfway, the finished work is lost and the
failed runs look like a bad reviewer. This keeps a checklist instead. After every scenario the result is written
down, and the next run carries on with what is still unchecked.

Three outcomes, not two. `pass` and `fail` are results: the reviewer did or did not behave as the example says, and
both get checked off. `error` is not a result: the run could not happen (quota gone, not logged in, CLI missing,
timeout). It stays unchecked and is retried, so running out of tokens never turns into "the reviewer failed".

Tool contract (Vegviser AI Tool Boundary)
  Classification:  Write, local only. Reads the bundle; writes its checklist under --state-dir (default
                   ~/.golden-path-harness/state/evals), outside every repo. It also SPENDS MODEL TOKENS: each scenario is a real
                   review through the chosen engine, and a critical scenario runs critical_repeats times.
  Owner:           team:teamvalue-aicoe. Version: the harness commit in .harness/VERSION.
  Caller identity: the engine CLI's own login, done by the user. This tool never logs in; on an authentication
                   error it stops and says so.
  Inputs:          run | status | reset, and the options below. Scenarios come from the bundle's examples, exactly
                   as eval.py builds them; scoring is eval.py's own (it is imported, not copied).
  Results:         a checklist (checklist.json, checklist.md) and, when every gating scenario is checked, the same
                   gate line eval.py prints. Exit 0 finished and the gate passes, 1 finished and it fails,
                   2 usage or the engine is unusable, 3 stopped before finishing (budget, login, repeated
                   errors, --limit, Ctrl-C): run the same command again to resume.
  Side effects:    the checklist files; every pass or fail is also written to tools/review/eval-results.jsonl, which
                   is committed so another machine resumes from it (summary only: scenario, status, short detail,
                   never model output; replay runs are not recorded); with --append-history, one line in tools/review/history.jsonl, only for a
                   complete run on a clean commit, as eval.py does. Raw model output is never stored.
  Review trigger:  a change to how eval.py builds or scores scenarios, or a new engine.

The checklist belongs to one engine, one model and one state of the bundle (a hash of the rules, examples, playbooks,
templates and review tools). Change any of them and a fresh checklist starts; the old one is kept, because its
results describe a reviewer that no longer exists.

Usage:
  eval-queue.py run [--engine copilot] [--limit 3] [--only NAME ...] [--no-advisory] [--retry-failed]
  eval-queue.py status        what is checked, what is left, what a full pass still costs
  eval-queue.py reset         throw this checklist away and start again
"""

import argparse
import concurrent.futures
import datetime
import functools
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import threading

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
BUNDLE_ROOT = HERE.parents[1]
DEFAULT_STATE = pathlib.Path(os.getenv("GOLDEN_PATH_HOME") or pathlib.Path.home() / ".golden-path-harness") / "state" / "evals"
DEFAULT_RESULTS = HERE / "eval-results.jsonl"   # committed, so a run started on one machine resumes on another
ENGINES = ["claude", "codex", "copilot", "agy", "replay"]

# What the reviewer is built from. A change to any of it makes earlier results about a different reviewer.
HASHED = ("index.md", "principles", "rules", "examples", "playbooks", "templates", "tools/review", "tools/harness/bundle.py")
SKIPPED = {"history.jsonl", "eval-results.jsonl", ".DS_Store", "eval-queue.py"}   # the queue is not part of the reviewer it measures

# The engines print free text on failure, so these are patterns, not an API. A miss only costs one more error
# before the consecutive-error stop, and the text is always shown.
BUDGET = re.compile(r"rate.?limit|quota|usage limit|too many requests|\b429\b|premium request|exhaust|billing|"
                    r"out of (credits|requests|tokens)|limit (reached|exceeded)|insufficient", re.I)
LOGIN = re.compile(r"not (logged|signed) in|log ?in required|(please|must) (log|sign) ?in|unauthori[sz]ed|\b401\b|"
                   r"\b403\b|copilot login|authentication|credentials?|token (expired|invalid)", re.I)
MARK = {"pass": "x", "fail": "!", "error": "?"}


def load_eval():
    """eval.py itself, so scenarios and scores cannot drift from the instrument."""
    spec = importlib.util.spec_from_file_location("harness_review_eval", HERE / "eval.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def clean(text, limit=300):
    return re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", str(text)).strip()[-limit:]


def bundle_hash(root):
    digest = hashlib.sha256()
    for part in HASHED:
        base = root / part
        files = [base] if base.is_file() else sorted(base.rglob("*")) if base.is_dir() else []
        for path in files:
            relative = path.relative_to(root)
            if not path.is_file() or "__pycache__" in relative.parts or path.name in SKIPPED:
                continue
            digest.update(relative.as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def scenarios_for(ev, root, thresholds, engine, only):
    """[(item, scenario tuple)] for the bundle's examples. An item says what the checklist needs to know."""
    found = []
    for scenario in ev.from_cases(root):
        name, spec = scenario[0], scenario[1]
        if only and name not in only:
            continue
        critical, advisory = bool(spec.get("critical")), bool(spec.get("advisory"))
        runs = thresholds["critical_repeats"] if critical and engine != "replay" else 1
        found.append(({"name": name, "critical": critical, "advisory": advisory, "runs": runs}, scenario))
    return found


def order(items):
    """Cheapest proof first, then what decides the gate, then the drafts.

    One cheap gating scenario goes first as a smoke test: if the setup is broken, it should cost one run, not
    the three a critical scenario takes. Advisory drafts last, because they cannot fail the gate."""
    gated = sorted((i for i in items if not i["advisory"]), key=lambda i: i["name"])
    smoke = next((i for i in gated if not i["critical"]), None)
    critical = [i for i in gated if i["critical"]]
    others = [i for i in gated if not i["critical"] and i is not smoke]
    drafts = sorted((i for i in items if i["advisory"]), key=lambda i: i["name"])
    return ([smoke] if smoke else []) + critical + others + drafts


def classify(result):
    """(status, detail). A run that errored is not a result."""
    if result.get("error"):
        return "error", clean(result["error"])
    if result["passed"]:
        return "pass", ""
    parts = []
    if result.get("missed"):
        parts.append(f"missed {result['missed']}")
    if result.get("false_positives"):
        parts.append(f"false positives {result['false_positives']}")
    if result.get("too_many"):
        parts.append(f"too many high-severity findings ({result.get('high_findings', 0)})")
    return "fail", clean("; ".join(parts) or "score did not pass")


def state_paths(state_dir, engine, model, digest):
    key = f"{engine}-{re.sub(r'[^A-Za-z0-9._-]', '_', model or 'default')}-{digest[:10]}"
    folder = state_dir / key
    return folder, folder / "checklist.json", folder / "checklist.md"


def load_state(path, engine, model, digest, thresholds, results=None):
    if path.is_file():
        state = json.loads(path.read_text(encoding="utf-8"))
    else:
        state = {"version": 1, "engine": engine, "model": model or "default", "bundle_hash": digest, "created": now(),
                 "thresholds": thresholds, "scenarios": {}}
    import_results(state, results)
    return state


def read_results(path):
    if not path or not path.is_file():
        return []
    lines = []
    for text in path.read_text(encoding="utf-8").splitlines():
        try:
            lines.append(json.loads(text))
        except ValueError:
            continue   # a half-merged line must not stop the queue; it is simply not a result
    return lines


def import_results(state, path):
    """Results committed from another machine count, if they describe this engine, model and bundle."""
    for line in read_results(path):
        if (line.get("engine"), line.get("model"), line.get("bundle_hash")) != (state["engine"], state["model"], state["bundle_hash"]):
            continue
        if line.get("status") in ("pass", "fail") and line.get("scenario") not in state["scenarios"]:
            state["scenarios"][line["scenario"]] = {
                "status": line["status"], "detail": line.get("detail", ""), "at": line.get("at", ""),
                "runs": line.get("runs", 1), "runs_passed": line.get("runs_passed"), "attempts": 0,
                "usage": line.get("usage"), "imported": True}


def record_result(path, state, name, entry):
    """Keep one line per scenario for this engine and model, and drop their lines for older bundles.

    Pass and fail only, never raw model output. Sorted, so two machines' additions merge without noise."""
    if state["engine"] == "replay" or entry["status"] not in ("pass", "fail"):
        return
    key = (state["engine"], state["model"])
    kept = [line for line in read_results(path)
            if (line.get("engine"), line.get("model")) != key]
    kept += [line for line in read_results(path)
             if (line.get("engine"), line.get("model")) == key and line.get("bundle_hash") == state["bundle_hash"]
             and line.get("scenario") != name]
    kept.append({"engine": state["engine"], "model": state["model"], "bundle_hash": state["bundle_hash"],
                 "scenario": name, "status": entry["status"], "detail": entry["detail"], "runs": entry["runs"],
                 "runs_passed": entry["runs_passed"], "at": entry["at"], "usage": entry.get("usage")})
    kept.sort(key=lambda l: (l["engine"], l["model"], l["scenario"]))
    write_atomic(path, "".join(json.dumps(l, sort_keys=True) + "\n" for l in kept))


def write_atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def progress(state, items):
    names = {i["name"] for i in items}
    entries = {n: s for n, s in state["scenarios"].items() if n in names}
    done = {n: s for n, s in entries.items() if s["status"] in ("pass", "fail")}
    counts = {"pass": 0, "fail": 0, "error": 0}
    for entry in entries.values():
        counts[entry["status"]] += 1
    pending = [i for i in items if i["name"] not in done]
    return done, counts, pending


def render_markdown(state, items):
    done, counts, pending = progress(state, items)
    runs_left = sum(i["runs"] for i in pending)
    lines = [f"# Reviewer evals: {state['engine']}, model {state['model']}, bundle {state['bundle_hash'][:10]}", "",
             f"Checked off {len(done)} of {len(items)} scenarios: {counts['pass']} pass, {counts['fail']} fail; "
             f"{counts['error']} could not run and will be retried. Still to run: {len(pending)} scenarios, "
             f"about {runs_left} reviews.", "",
             f"Spent so far: {spent(state, items, ev_usage())}.", "",
             "`[x]` pass   `[!]` fail (the reviewer was wrong, a real result)   `[?]` could not run   `[ ]` not run yet", ""]
    for title, wanted in (("Gating", False), ("Drafts (advisory, cannot fail the gate)", True)):
        group = [i for i in items if i["advisory"] == wanted]
        if not group:
            continue
        lines += [f"## {title}", ""]
        for item in group:
            entry = state["scenarios"].get(item["name"])
            box = MARK[entry["status"]] if entry else " "
            tag = f" (critical, {item['runs']} runs)" if item["critical"] else ""
            note = f" - {entry['status'].upper()}: {entry['detail']}" if entry and entry["detail"] else ""
            lines.append(f"- [{box}] {item['name']}{tag}{note}")
        lines.append("")
    return "\n".join(lines)


def save(state, items, json_path, md_path):
    write_atomic(json_path, json.dumps(state, indent=2) + "\n")
    write_atomic(md_path, render_markdown(state, items))


@functools.lru_cache(maxsize=None)
def ev_usage():
    """usage.py, the same module the adapters write with; loaded once."""
    spec = importlib.util.spec_from_file_location("review_usage", HERE / "usage.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def usage_total(state, items, usage):
    """Tokens, cost and time of every scenario in this checklist that has a result, drafts included."""
    entries = state["scenarios"]
    return usage.total(entries[i["name"]].get("usage") or {"runs": entries[i["name"]].get("runs", 1)}
                       for i in items if entries.get(i["name"], {}).get("status") in ("pass", "fail"))


def spent(state, items, usage):
    return usage.describe(usage_total(state, items, usage))


def verdict(state, items, partial):
    """The gate, as eval.py computes it, once every gating scenario has a result."""
    gated = [i for i in items if not i["advisory"]]
    entries = state["scenarios"]
    if any(entries.get(i["name"], {}).get("status") not in ("pass", "fail") for i in gated):
        return None
    passed = sum(entries[i["name"]]["status"] == "pass" for i in gated)
    critical_failures = [i["name"] for i in gated if i["critical"] and entries[i["name"]]["status"] == "fail"]
    rate = passed / len(gated) if gated else 0.0
    limits = state["thresholds"]
    gate = not critical_failures and rate >= limits["min_pass_rate"] and (partial or len(gated) >= limits["min_scenarios"])
    drafts = [i["name"] for i in items if i["advisory"]]
    draft_failed = [n for n in drafts if entries.get(n, {}).get("status") == "fail"]
    return {"scenarios": len(gated), "passed": passed, "pass_rate": round(rate, 3), "critical_failures": critical_failures,
            "partial": partial, "advisory": {"scenarios": len(drafts), "failed": draft_failed},
            "gate": "pass" if gate else "fail", "failed": [i["name"] for i in gated if entries[i["name"]]["status"] == "fail"],
            "usage": usage_total(state, items, ev_usage())}


def append_history(ev, state, result):
    # eval-results.jsonl and history.jsonl are this tool's own output; changes to them alone do not make it dirty.
    commit, dirty = ev.harness_commit(BUNDLE_ROOT)
    if state["engine"] == "replay" or result["partial"] or dirty:
        why = ("a replay run" if state["engine"] == "replay" else "a partial run" if result["partial"]
               else "the harness has uncommitted changes")
        print(f"history.jsonl not appended: {why}. Only a complete run on a clean commit counts as evidence.")
        return
    cli = shutil.which(state["engine"]) or state["engine"]
    version = subprocess.run([cli, "--version"], capture_output=True, text=True).stdout.strip()
    line = {"harness": commit, "engine_version": version, "model": state["model"], "at": now()}
    line.update({k: result[k] for k in ("scenarios", "passed", "pass_rate", "critical_failures", "partial", "advisory", "gate")},
                failed=result["failed"], usage=result["usage"])
    with (HERE / "history.jsonl").open("a", encoding="utf-8") as history:
        history.write(json.dumps(line) + "\n")
    print("appended harness/tools/review/history.jsonl; commit it with the harness change")


def context(args):
    ev = load_eval()
    bundle = args.bundle.resolve()
    thresholds = json.loads(args.thresholds.read_text(encoding="utf-8"))
    digest = bundle_hash(bundle)
    only = set(args.only or [])
    pairs = scenarios_for(ev, bundle, thresholds, args.engine, only)
    unknown = sorted(only - {item["name"] for item, _ in pairs})
    if unknown:
        known = ", ".join(sorted(item["name"] for item, _ in scenarios_for(ev, bundle, thresholds, args.engine, set())))
        print(f"eval-queue: no such scenario: {', '.join(unknown)}\nknown: {known}", file=sys.stderr)
        sys.exit(2)
    folder, json_path, md_path = state_paths(args.state_dir.expanduser(), args.engine, args.model, digest)
    return ev, thresholds, digest, pairs, folder, json_path, md_path


def cmd_status(args):
    ev, thresholds, digest, pairs, folder, json_path, md_path = context(args)
    items = order([item for item, _ in pairs])
    state = load_state(json_path, args.engine, args.model, digest, thresholds, args.results_file)
    print(render_markdown(state, items))
    older = [p.name for p in args.state_dir.expanduser().glob(f"{args.engine}-*") if p.is_dir() and p != folder]
    if older:
        print(f"Older checklists for earlier states of the bundle are kept and not used: {', '.join(sorted(older))}")
    print(f"checklist: {md_path}")
    return 0


def cmd_reset(args):
    _, _, _, _, folder, json_path, md_path = context(args)
    removed = [p.name for p in (json_path, md_path) if p.is_file()]
    for path in (json_path, md_path):
        path.unlink(missing_ok=True)
    print(f"removed {', '.join(removed)}" if removed else "nothing to remove")
    return 0


def stop(message, state, items, json_path, md_path):
    save(state, items, json_path, md_path)
    print(f"\n{message}\nNothing was checked off for the scenario that stopped. Resume with the same command:\n"
          f"  {' '.join(shlex.quote(a) for a in [sys.executable, *sys.argv])}\nchecklist: {md_path}")
    return 3


def cmd_run(args):
    ev, thresholds, digest, pairs, folder, json_path, md_path = context(args)
    by_name = {item["name"]: scenario for item, scenario in pairs}
    items = order([item for item, _ in pairs])
    run_args = argparse.Namespace(engine=args.engine, model=args.model, replay_dir=args.replay_dir, jobs=args.jobs,
                                  bundle=args.bundle.resolve())
    preflight = ev.engine_preflight_error(run_args)
    if preflight:
        print(f"eval-queue: {preflight}", file=sys.stderr)
        return 2
    state = load_state(json_path, args.engine, args.model, digest, thresholds, args.results_file)
    older = [p.name for p in args.state_dir.expanduser().glob(f"{args.engine}-*") if p.is_dir() and p != folder]
    if older and not json_path.is_file():
        print(f"Starting a new checklist: the bundle, engine or model changed since {', '.join(sorted(older))}, "
              "whose results describe a different reviewer. They are kept, not used.")

    def wanted(item):
        entry = state["scenarios"].get(item["name"])
        if args.no_advisory and item["advisory"]:
            return False
        return entry is None or entry["status"] == "error" or (entry["status"] == "fail" and args.retry_failed)

    queue = [item for item in items if wanted(item)]
    print(f"{len(items) - len(queue)} of {len(items)} scenarios already have a result; "
          f"{len(queue)} to run, about {sum(i['runs'] for i in queue)} reviews with {args.engine}.")
    print(f"checklist: {md_path}")
    save(state, items, json_path, md_path)

    if args.jobs == 1:
        consecutive_errors, ran = 0, 0
        for position, item in enumerate(queue, 1):
            if args.limit and ran >= args.limit:
                return stop(f"Stopped after {ran} scenario(s) as --limit asked.", state, items, json_path, md_path)
            proven = any(e["status"] in ("pass", "fail") for e in state["scenarios"].values())
            tag = f" (critical, {item['runs']} runs)" if item["critical"] else ""
            print(f"\n[{position}/{len(queue)}] {item['name']}{tag}", flush=True)
            try:
                result = ev.run_scenarios([by_name[item["name"]]], run_args, thresholds)[0]
                status, detail = classify(result)
            except KeyboardInterrupt:
                return stop("Interrupted.", state, items, json_path, md_path)
            except Exception as error:  # a crash in one scenario must not lose the others' results
                status, detail = "error", clean(f"{type(error).__name__}: {error}")
            ran += 1
            previous = state["scenarios"].get(item["name"], {})
            state["scenarios"][item["name"]] = {
                "status": status, "detail": detail, "at": now(), "runs": item["runs"],
                "runs_passed": result.get("runs_passed") if status != "error" else None,
                "attempts": previous.get("attempts", 0) + 1, "usage": result.get("usage")}
            save(state, items, json_path, md_path)
            record_result(args.results_file, state, item["name"], state["scenarios"][item["name"]])
            print(f"  -> {status}{': ' + detail if detail else ''}")
            if status != "error":
                consecutive_errors = 0
                continue
            consecutive_errors += 1
            if BUDGET.search(detail):
                return stop("This looks like the model budget or quota running out. Wait for it to reset, then resume.",
                            state, items, json_path, md_path)
            if LOGIN.search(detail):
                return stop(f"This looks like a login problem. Log in to {args.engine} yourself, then resume.",
                            state, items, json_path, md_path)
            if not proven or consecutive_errors >= args.max_errors:
                reason = ("Nothing has run successfully yet, so the setup is the likely problem; fix it before spending more."
                          if not proven else f"{consecutive_errors} errors in a row.")
                return stop(f"Stopping. {reason}", state, items, json_path, md_path)
    else:
        state_lock = threading.Lock()
        consecutive_errors, ran = 0, 0
        stop_early = None
        queue_iter = iter(enumerate(queue, 1))

        def execute_item(item):
            item_run_args = argparse.Namespace(**vars(run_args))
            item_run_args.jobs = 1
            try:
                res = ev.run_scenarios([by_name[item["name"]]], item_run_args, thresholds)[0]
                st, det = classify(res)
                return item, st, det, res
            except Exception as error:
                return item, "error", clean(f"{type(error).__name__}: {error}"), {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
            active_futures = {}

            while len(active_futures) < args.jobs:
                if args.limit and ran + len(active_futures) >= args.limit:
                    break
                try:
                    pos, item = next(queue_iter)
                    tag = f" (critical, {item['runs']} runs)" if item["critical"] else ""
                    print(f"[{pos}/{len(queue)}] {item['name']}{tag}", flush=True)
                    f = executor.submit(execute_item, item)
                    active_futures[f] = (pos, item)
                except StopIteration:
                    break

            while active_futures and not stop_early:
                done, _ = concurrent.futures.wait(active_futures.keys(), return_when=concurrent.futures.FIRST_COMPLETED)
                for f in done:
                    pos, item = active_futures.pop(f)
                    ran += 1
                    try:
                        item, status, detail, result = f.result()
                    except Exception as error:
                        item, status, detail, result = item, "error", clean(f"{type(error).__name__}: {error}"), {}

                    with state_lock:
                        previous = state["scenarios"].get(item["name"], {})
                        state["scenarios"][item["name"]] = {
                            "status": status, "detail": detail, "at": now(), "runs": item["runs"],
                            "runs_passed": result.get("runs_passed") if status != "error" else None,
                            "attempts": previous.get("attempts", 0) + 1, "usage": result.get("usage")}
                        save(state, items, json_path, md_path)
                        record_result(args.results_file, state, item["name"], state["scenarios"][item["name"]])
                        print(f"  -> {item['name']}: {status}{': ' + detail if detail else ''}", flush=True)

                        proven = any(e["status"] in ("pass", "fail") for e in state["scenarios"].values())
                        if status != "error":
                            consecutive_errors = 0
                        else:
                            consecutive_errors += 1
                            if BUDGET.search(detail):
                                stop_early = "This looks like the model budget or quota running out. Wait for it to reset, then resume."
                                break
                            if LOGIN.search(detail):
                                stop_early = f"This looks like a login problem. Log in to {args.engine} yourself, then resume."
                                break
                            if not proven or consecutive_errors >= args.max_errors:
                                reason = ("Nothing has run successfully yet, so the setup is the likely problem; fix it before spending more."
                                          if not proven else f"{consecutive_errors} errors in a row.")
                                stop_early = f"Stopping. {reason}"
                                break

                    if not stop_early:
                        if not args.limit or ran + len(active_futures) < args.limit:
                            try:
                                next_pos, next_item = next(queue_iter)
                                next_tag = f" (critical, {next_item['runs']} runs)" if next_item["critical"] else ""
                                print(f"[{next_pos}/{len(queue)}] {next_item['name']}{next_tag}", flush=True)
                                next_f = executor.submit(execute_item, next_item)
                                active_futures[next_f] = (next_pos, next_item)
                            except StopIteration:
                                pass

            if stop_early:
                for f in active_futures:
                    f.cancel()
                executor.shutdown(wait=False, cancel_futures=True)
                return stop(stop_early, state, items, json_path, md_path)

            if args.limit and ran >= args.limit and any(i["name"] not in state["scenarios"] for i in queue):
                return stop(f"Stopped after {ran} scenario(s) as --limit asked.", state, items, json_path, md_path)

    result = verdict(state, items, partial=bool(args.only))
    done, counts, pending = progress(state, items)
    skipped_drafts = [i for i in pending if i["advisory"] and args.no_advisory]
    left = [i for i in pending if i not in skipped_drafts]
    if result is None or left:
        return stop(f"{len(left)} scenario(s) still have no result.", state, items, json_path, md_path)
    print(f"\n{result['passed']}/{result['scenarios']} passed, critical failures: {result['critical_failures'] or 'none'}, "
          f"gate: {result['gate']}")
    print(f"advisory (drafts, not gating): {result['advisory']['scenarios'] - len(result['advisory']['failed'])}/"
          f"{result['advisory']['scenarios']} passed"
          + (f", failed: {result['advisory']['failed']}" if result["advisory"]["failed"] else "")
          + (f" ({len(skipped_drafts)} drafts skipped)" if skipped_drafts else ""))
    print(f"usage: {ev.usage.describe(result['usage'])}")
    print(f"checklist: {md_path}")
    if args.append_history:
        append_history(ev, state, result)
    return 0 if result["gate"] == "pass" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", nargs="?", default="run", choices=["run", "status", "reset"])
    parser.add_argument("--engine", default="copilot", choices=ENGINES)
    parser.add_argument("--model", help="model to pin; a different model is a different checklist")
    parser.add_argument("--replay-dir")
    parser.add_argument("--only", action="append", help="only this scenario (repeatable); the run is partial")
    parser.add_argument("--jobs", type=int, default=1,
                        help="maximum concurrent eval runs per scenario (default: 1, max: 8)")
    parser.add_argument("--limit", type=int, default=0, help="stop after this many scenarios, to spread tokens over days")
    parser.add_argument("--no-advisory", action="store_true", help="skip the draft examples, which cannot fail the gate")
    parser.add_argument("--retry-failed", action="store_true",
                        help="run scenarios that failed again; the reviewer is not deterministic")
    parser.add_argument("--max-errors", type=int, default=2, help="stop after this many errors in a row (default 2)")
    parser.add_argument("--append-history", action="store_true",
                        help="when every gating scenario is checked, record the run in history.jsonl as eval.py does")
    parser.add_argument("--state-dir", type=pathlib.Path, default=DEFAULT_STATE)
    parser.add_argument("--results-file", type=pathlib.Path, default=DEFAULT_RESULTS,
                        help="committed pass/fail results shared between machines (default: eval-results.jsonl)")
    parser.add_argument("--bundle", type=pathlib.Path, default=BUNDLE_ROOT)
    parser.add_argument("--thresholds", type=pathlib.Path, default=HERE / "thresholds.json")
    args = parser.parse_args()
    if args.limit < 0 or args.max_errors < 1 or not 1 <= args.jobs <= 8:
        parser.error("--limit must be 0 or more, --max-errors 1 or more, and --jobs between 1 and 8")
    return {"run": cmd_run, "status": cmd_status, "reset": cmd_reset}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
