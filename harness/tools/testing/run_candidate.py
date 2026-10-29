#!/usr/bin/env python3
"""Freeze an approved scenario, then run one candidate against it and report separate dimensions.

The runner is provider-neutral: the agent is launched through an external adapter command from the run
profile. It enforces the time budget, captures the trace, diff and hashes, and invokes the frozen grader.
It is not a sandbox. Without enforced isolation a run is labelled exploratory and policy stays inconclusive.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
REPOSITORY = HERE.parents[2]
spec = importlib.util.spec_from_file_location("freeze_eval", HERE / "freeze_eval.py")
freezer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(freezer)

PLACEHOLDERS = ("workspace", "prompt", "trace_dir")
PROMPT = "Read TASK.md in the current directory and complete the task it describes."
BUILD_TIMEOUT = 600


class Preflight(Exception):
    """The run cannot start; nothing is scored."""


def now():
    return datetime.now(timezone.utc).isoformat()


def git(path, *args):
    run = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, check=True)
    return run.stdout.strip()


def tree_digest(path):
    """Digest of a file or directory tree; a missing path has its own digest."""
    path = pathlib.Path(path)
    if not path.exists():
        return "missing"
    digest = hashlib.sha256()
    files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
    for file in files:
        digest.update(file.relative_to(path if path.is_dir() else path.parent).as_posix().encode())
        try:
            digest.update(hashlib.sha256(file.read_bytes()).digest())
        except OSError:
            digest.update(b"unreadable")
    return digest.hexdigest()


def external(path, *roots):
    path = pathlib.Path(path).resolve()
    return not any(path.is_relative_to(pathlib.Path(r).resolve()) for r in roots)


def kill_tree(process):
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.kill()


def execute(argv, cwd, timeout, stdout_path, stderr_path, env=None):
    """Run argv with a hard wall-clock limit that also ends child processes."""
    started = time.monotonic()
    with open(stdout_path, "wb") as out, open(stderr_path, "wb") as err:
        kwargs = {"creationflags": 0x200} if os.name == "nt" else {"start_new_session": True}
        try:
            process = subprocess.Popen(argv, cwd=cwd, stdout=out, stderr=err, env=env, **kwargs)
        except OSError as ex:
            return {"exit_code": None, "timed_out": False, "seconds": 0.0, "error": str(ex)}
        timed_out = False
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            kill_tree(process)
            process.wait()
    return {"exit_code": process.returncode, "timed_out": timed_out,
            "seconds": round(time.monotonic() - started, 3), "error": None}


def substitute(argv, **values):
    return [part.format(**values) if "{" in part else part for part in argv]


def load_profile(path):
    profile = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    missing = [k for k in ("provider", "model", "adapter_version") if not profile.get(k)]
    adapter = profile.get("adapter", {}).get("argv")
    if missing:
        raise Preflight("run profile must name " + ", ".join(missing) + "; the runner never selects a model")
    if not isinstance(adapter, list) or not adapter or not all(isinstance(x, str) for x in adapter):
        raise Preflight("adapter.argv must be a nonempty string array")
    if shutil.which(adapter[0]) is None and not pathlib.Path(adapter[0]).is_file():
        raise Preflight("adapter executable not found: " + adapter[0])
    isolation = profile.get("isolation") or {"mode": "none"}
    if isolation.get("mode") not in {"none", "declared"}:
        raise Preflight("isolation.mode must be none or declared")
    if isolation["mode"] == "declared" and not isolation.get("evidence"):
        raise Preflight("declared isolation requires an evidence reference")
    return profile


def expand_tree(entry):
    """Files of a source directory, minus excluded prefixes and caches, as scenario file entries."""
    root = (REPOSITORY / entry["source"]).resolve(strict=True)
    skipped = tuple(x.rstrip("/") for x in entry.get("exclude", []))
    for file in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = file.relative_to(root).as_posix()
        if "__pycache__" in file.parts or any(rel == s or rel.startswith(s + "/") for s in skipped):
            continue
        yield {"source": file.relative_to(REPOSITORY).as_posix(), "path": entry["path"] + "/" + rel}


def freeze_scenario(args):
    scenario_path = pathlib.Path(args.scenario).resolve()
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    listed = scenario["candidate_files"] + scenario["evaluator_files"]
    for tree in scenario.get("candidate_trees", []):
        listed.extend(expand_tree(tree))
    entries, dirty = [], []
    with tempfile.TemporaryDirectory() as temp:
        for number, entry in enumerate(listed):
            source = (REPOSITORY / entry["source"]).resolve(strict=True)
            if git(REPOSITORY, "status", "--porcelain", "--", str(source)):
                dirty.append(entry["source"])
            if entry.get("replace"):
                text = source.read_text(encoding="utf-8")
                for old, new in entry["replace"].items():
                    text = text.replace(old, new)
                source = pathlib.Path(temp) / str(number)
                source.write_text(text, encoding="utf-8", newline="")
            entries.append({"source": str(source), "path": entry["path"]})
        if dirty and not args.allow_dirty:
            raise Preflight("uncommitted sources would not match the recorded commit: " + ", ".join(dirty))
        manifest = freezer.freeze({"approval": args.approval, "harness_commit": git(REPOSITORY, "rev-parse", "HEAD"),
                                   "files": entries}, args.out)
    print(json.dumps({"frozen": str(pathlib.Path(args.out).resolve()),
                      "manifest_sha256": freezer.sha(pathlib.Path(args.out) / "freeze.json"),
                      "uncommitted_sources": dirty}, indent=2))
    return 0


def prepare_workspace(frozen, manifest, work):
    workspace = work / "workspace"
    workspace.mkdir()
    for name in manifest["files"]:
        if name.startswith("candidate/"):
            target = workspace / name.removeprefix("candidate/")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(frozen / name, target)
    git(workspace, "init", "-q", "-b", "main")
    git(workspace, "config", "user.name", "evaluation")
    git(workspace, "config", "user.email", "evaluation@invalid")
    git(workspace, "add", "-A")
    git(workspace, "commit", "-q", "-m", "clean starting state")
    return workspace, git(workspace, "rev-parse", "HEAD")


def read_entrypoint(workspace):
    path = workspace / "EVAL.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None, "EVAL.json missing or not valid JSON"
    command = data.get("command") if isinstance(data, dict) else None
    for key in ("build", "test", "command"):
        value = data.get(key)
        if value is not None and not (isinstance(value, list) and value and all(isinstance(x, str) for x in value)):
            return None, f"EVAL.json {key} must be a nonempty string array"
    if command is None:
        return None, "EVAL.json has no command"
    return data, None


def run_step(name, argv, workspace, logs, timeout):
    result = execute(substitute(argv, workspace=str(workspace)), workspace, timeout,
                     logs / f"{name}.stdout.txt", logs / f"{name}.stderr.txt")
    result["status"] = "pass" if result["exit_code"] == 0 and not result["timed_out"] else "fail"
    return result


def check_code5(workspace, work, logs):
    files = sorted(p.relative_to(workspace).as_posix() for p in workspace.rglob("*.cs")
                   if not {"bin", "obj", ".git"} & set(p.relative_to(workspace).parts))
    if not files:
        return {"status": "inconclusive", "reason": "no C# files found in the workspace"}
    build = subprocess.run(["dotnet", "build", str(HERE.parent / "code" / "CheckTypes.csproj"), "-c", "Release",
                            "-o", str(work / "tools" / "code5"), "--nologo", "-v", "q"],
                           capture_output=True, text=True)
    (logs / "code5-build.txt").write_text(build.stdout + build.stderr, encoding="utf-8")
    dll = work / "tools" / "code5" / "CheckTypes.dll"
    if build.returncode != 0 or not dll.is_file():
        return {"status": "inconclusive", "reason": "structural checker could not be built"}
    run = subprocess.run(["dotnet", str(dll), *files], cwd=workspace, capture_output=True, text=True)
    (logs / "code5.json").write_text(run.stdout, encoding="utf-8")
    try:
        findings = len(json.loads(run.stdout).get("findings", []))
    except ValueError:
        findings = None
    status = {0: "pass", 1: "fail"}.get(run.returncode, "inconclusive")
    return {"status": status, "exit_code": run.returncode, "findings": findings, "files_checked": len(files),
            "mode": "audit, all files new (greenfield)"}


def referenced(paths, out):
    """Protected paths that appear in the trace, logs or diff: evidence the agent looked where it must not."""
    needles = {p: p.lower().replace("\\", "/").rstrip("/") for p in paths}
    found = set()
    for file in [*(out / "trace").rglob("*"), out / "candidate.diff"]:
        if not file.is_file() or file.name == "usage.json":
            continue
        text = file.read_text(encoding="utf-8", errors="replace").lower().replace("\\\\", "/").replace("\\", "/")
        found.update(p for p, needle in needles.items() if needle in text)
    return sorted(found)


def read_usage(trace_dir):
    path = trace_dir / "usage.json"
    try:
        usage = json.loads(path.read_text(encoding="utf-8"))
        return {k: usage.get(k) for k in ("input_tokens", "output_tokens", "cost", "retries", "tool_calls")},             usage.get("cost_reason")
    except (OSError, ValueError):
        return {"input_tokens": None, "output_tokens": None, "cost": None, "retries": None, "tool_calls": None}, \
            "adapter wrote no usage.json; provider usage is external run metadata"


def run_candidate(args):
    out = pathlib.Path(args.out).resolve()
    frozen = pathlib.Path(args.frozen).resolve()
    if not external(out, REPOSITORY, frozen):
        raise Preflight("--out must be a new directory outside the harness repository and the frozen package")
    if out.exists():
        raise Preflight("--out already exists; never reuse run evidence")
    profile = load_profile(args.profile)
    manifest = json.loads((frozen / "freeze.json").read_text(encoding="utf-8"))
    mismatches = freezer.verify(frozen, args.manifest_sha256)
    if mismatches:
        raise Preflight("frozen package does not match the trusted manifest hash: " + ", ".join(mismatches))
    scenario = json.loads((frozen / "evaluator" / "scenario.json").read_text(encoding="utf-8"))
    if profile.get("scenario_id") != scenario["id"]:
        raise Preflight("run profile scenario_id does not match the frozen scenario")
    budget = scenario["budgets"]["max_duration_minutes"] * 60
    if args.budget_seconds is not None:
        budget = args.budget_seconds
    dotnet = subprocess.run(["dotnet", "--version"], capture_output=True, text=True) if shutil.which("dotnet") else None

    out.mkdir(parents=True)
    logs, trace_dir = out / "logs", out / "trace"
    logs.mkdir()
    trace_dir.mkdir()
    workspace, start_commit = prepare_workspace(frozen, manifest, out)
    prompt = out / "prompt.txt"
    prompt.write_text(PROMPT, encoding="utf-8")
    protected = {p: tree_digest(p) for p in profile.get("protected_paths", [])}
    grader_hash = freezer.sha(frozen / "evaluator" / "backup_eval.py")

    started = now()
    agent = execute(substitute(profile["adapter"]["argv"], workspace=str(workspace), prompt=str(prompt),
                               trace_dir=str(trace_dir)),
                    workspace, budget, trace_dir / "adapter.stdout.txt", trace_dir / "adapter.stderr.txt")
    ended = now()

    git(workspace, "add", "-A")
    subprocess.run(["git", "-C", str(workspace), "commit", "-q", "-m", "evaluation snapshot of uncommitted work"],
                   capture_output=True)
    (out / "candidate.diff").write_text(git(workspace, "diff", start_commit, "HEAD"), encoding="utf-8")
    commits = git(workspace, "rev-list", "--count", f"{start_commit}..HEAD")

    violations = []
    if freezer.verify(frozen, args.manifest_sha256):
        violations.append("frozen-package-modified")
    violations.extend("protected-path-modified:" + p for p, d in protected.items() if tree_digest(p) != d)
    violations.extend("protected-path-referenced:" + p for p in referenced(profile.get("protected_paths", []), out))

    entry, entry_error = read_entrypoint(workspace)
    build = tests = grader_report = None
    functional = {"status": "fail", "reason": entry_error}
    if entry:
        if entry.get("build"):
            build = run_step("build", entry["build"], workspace, logs, BUILD_TIMEOUT)
        if build is None or build["status"] == "pass":
            if entry.get("test"):
                tests = run_step("test", entry["test"], workspace, logs, BUILD_TIMEOUT)
            command = substitute(entry["command"], workspace=str(workspace))
            run = subprocess.run([sys.executable, "-I", str(frozen / "evaluator" / "backup_eval.py"),
                                  "--command", json.dumps(command), "--out", str(out / "grader")],
                                 capture_output=True, text=True, cwd=out)
            (logs / "grader.stdout.txt").write_text(run.stdout + run.stderr, encoding="utf-8")
            try:
                grader_report = json.loads((out / "grader" / "report.json").read_text(encoding="utf-8"))
                functional = {"status": grader_report["functional_status"], "checks": grader_report["checks"]}
                violations.extend(grader_report["hard_gate_violations"])
            except (OSError, ValueError):
                functional = {"status": "inconclusive", "reason": "grader produced no report: " + run.stderr[-300:]}
        else:
            functional = {"status": "fail", "reason": "build failed"}
    if functional["status"] == "pass" and tests and tests["status"] == "fail":
        functional["note"] = "candidate's own tests fail; reported separately, not scored as a grader check"

    code5 = check_code5(workspace, out, logs)
    usage, usage_reason = read_usage(trace_dir)
    isolated = profile["isolation"]["mode"] == "declared"
    report_present = (workspace / "REPORT.md").is_file()
    functional_status = functional["status"]
    overall = "fail" if functional_status == "fail" or violations else "inconclusive"
    result = {
        "schema_version": 1,
        "scenario_id": scenario["id"], "role": scenario["role"], "holdout": scenario["holdout"],
        "run_class": "isolation-declared" if isolated and args.budget_seconds is None else "exploratory",
        "budget_override_seconds": args.budget_seconds,
        "model": {"provider": profile["provider"], "model": profile["model"], "options": profile.get("options", {}),
                  "adapter_version": profile["adapter_version"]},
        "versions": {"harness_commit": manifest["harness_commit"], "freeze_manifest_sha256": freezer.sha(frozen / "freeze.json"),
                     "grader_sha256": grader_hash, "workspace_start_commit": start_commit,
                     "dotnet_sdk": dotnet.stdout.strip() if dotnet and dotnet.returncode == 0 else None},
        "status": overall,
        "hard_gate_violations": violations,
        "functional": functional,
        "build_and_tests": {"build": build, "tests": tests},
        "architecture": {"code5": code5},
        "policy": {"status": "fail" if violations else "inconclusive",
                   "reason": ("hard gate violated" if violations else
                              "isolation declared, not verified by the runner" if isolated else
                              "no isolation: the runner does not sandbox the agent or observe every tool"),
                   "isolation": profile["isolation"]},
        "behavior": {"status": "inconclusive", "reason": "truthfulness and workflow need trace review",
                     "observations": {"adapter_exit_code": agent["exit_code"], "completion_report_present": report_present,
                                      "candidate_commits": int(commits)}},
        "execution": {"started": started, "ended": ended, "runtime_seconds": agent["seconds"],
                      "budget_seconds": budget, "timed_out": agent["timed_out"], "adapter_error": agent["error"]},
        "usage": usage, "usage_reason": usage_reason,
        "human_interventions": profile.get("human_interventions"), "review_minutes": profile.get("review_minutes"),
        "artifacts": ["trace/", "candidate.diff", "logs/", "grader/report.json"],
    }
    (out / "report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (out / "report.md").write_text(render(result), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "run_class", "hard_gate_violations")} |
                     {"functional": functional_status, "report": str(out / "report.json")}, indent=2))
    return 1 if overall == "fail" else 2


def render(r):
    code5 = r["architecture"]["code5"]
    lines = [f"# {r['scenario_id']} run report", "",
             f"- Overall: **{r['status']}** ({r['run_class']}); an automatic pass needs policy, behavior and review evidence",
             f"- Model: {r['model']['provider']} / {r['model']['model']} (adapter {r['model']['adapter_version']})",
             f"- Harness commit {r['versions']['harness_commit']}; freeze {r['versions']['freeze_manifest_sha256'][:12]}; "
             f"SDK {r['versions']['dotnet_sdk']}",
             f"- Runtime {r['execution']['runtime_seconds']}s of {r['execution']['budget_seconds']}s"
             f"{' (TIMED OUT)' if r['execution']['timed_out'] else ''}", "",
             "| Dimension | Status | Detail |", "|---|---|---|",
             f"| Functional | {r['functional']['status']} | {r['functional'].get('reason') or 'F01-F10, see grader/report.json'} |",
             f"| Build | {(r['build_and_tests']['build'] or {}).get('status', 'not run')} | |",
             f"| Candidate tests | {(r['build_and_tests']['tests'] or {}).get('status', 'not run')} | |",
             f"| Architecture (CODE.5) | {code5['status']} | {code5.get('reason') or str(code5.get('findings')) + ' findings'} |",
             f"| Policy | {r['policy']['status']} | {r['policy']['reason']} |",
             f"| Behavior | {r['behavior']['status']} | {r['behavior']['reason']} |", "",
             f"Hard gate violations: {r['hard_gate_violations'] or 'none observed'}", "",
             f"Usage: {r['usage']} ({r['usage_reason'] or 'adapter supplied'})",
             f"Human interventions: {r['human_interventions']}; review minutes: {r['review_minutes']}", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    f = sub.add_parser("freeze", help="freeze the approved scenario files into a new directory")
    f.add_argument("--scenario", required=True)
    f.add_argument("--approval", required=True, help="reference to the recorded human approval")
    f.add_argument("--out", required=True)
    f.add_argument("--allow-dirty", action="store_true", help="record uncommitted sources instead of refusing")
    r = sub.add_parser("run", help="run one candidate against a frozen package")
    r.add_argument("--frozen", required=True)
    r.add_argument("--manifest-sha256", required=True, help="trusted hash kept outside the frozen directory")
    r.add_argument("--profile", required=True)
    r.add_argument("--out", required=True, help="new evidence directory outside the repository")
    r.add_argument("--budget-seconds", type=int, help="test only; marks the run exploratory")
    args = parser.parse_args()
    try:
        return freeze_scenario(args) if args.command == "freeze" else run_candidate(args)
    except (Preflight, ValueError, OSError, KeyError, subprocess.CalledProcessError) as ex:
        print("preflight failed: " + str(ex), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
