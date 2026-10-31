#!/usr/bin/env python3
"""Evaluate reviewer behavior from human-readable harness examples.

Each example becomes a throwaway git repo with .harness/ copied in; review.sh is the same script
the PR pipeline runs. Human-verified examples and reviewer-behavior examples gate. Other drafts are evaluated and reported as
advisory: a draft is not precedent for the reviewer and cannot fail the gate, but a failure is visible.

Run with: python3 -I harness/tools/review/eval.py
"""

import argparse
import datetime
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = pathlib.Path(__file__).resolve().parent
# Same layout rule as bundle.py: tools/review/ sits two levels under the bundle root, wherever the bundle lives.
BUNDLE_ROOT = HERE.parents[1]
DEFAULT_BUNDLE = BUNDLE_ROOT
# Keep identical to CLI_ENVIRONMENT in run-claude.py (tests/test_eval.py checks it).
CLI_ENVIRONMENT = ("PATH", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "TMP", "TMPDIR", "TEMP",
                   "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT",
                   "LANG", "LC_ALL", "LC_CTYPE", "TERM", "CI", "CLAUDE_CONFIG_DIR",
                   "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL",
                   "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "AWS_REGION", "AWS_DEFAULT_REGION",
                   "AWS_BEARER_TOKEN_BEDROCK", "ANTHROPIC_VERTEX_PROJECT_ID", "CLOUD_ML_REGION",
                   "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "SSL_CERT_FILE", "NODE_EXTRA_CA_CERTS")
COPILOT_CLI_ENVIRONMENT = ("PATH", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "TMP", "TMPDIR", "TEMP",
                           "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT",
                           "LANG", "LC_ALL", "LC_CTYPE", "TERM", "CI", "COPILOT_HOME", "HTTPS_PROXY",
                           "HTTP_PROXY", "NO_PROXY", "SSL_CERT_FILE", "NODE_EXTRA_CA_CERTS")
# Keep identical to CLI_ENVIRONMENT in run-codex.py.
CODEX_CLI_ENVIRONMENT = ("PATH", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "TMP", "TMPDIR", "TEMP",
                         "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "CODEX_HOME",
                         "LANG", "LC_ALL", "LC_CTYPE", "TERM", "CI", "OPENAI_API_KEY", "OPENAI_BASE_URL",
                         "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "SSL_CERT_FILE", "NODE_EXTRA_CA_CERTS")
# Keep identical to CLI_ENVIRONMENT in run-agy.py.
AGY_CLI_ENVIRONMENT = ("PATH", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "TMP", "TMPDIR", "TEMP",
                       "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT",
                       "LANG", "LC_ALL", "LC_CTYPE", "TERM", "CI", "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY",
                       "SSL_CERT_FILE", "NODE_EXTRA_CA_CERTS")
LANG_EXT = {"csharp": "cs", "cs": "cs", "bicep": "bicep", "hcl": "tf", "terraform": "tf", "typescript": "ts",
            "ts": "ts", "javascript": "js", "python": "py", "bash": "sh", "shell": "sh", "yaml": "yml", "json": "json"}
LINE_TOLERANCE = 3
HIGH = {"blocker", "major"}

sys.dont_write_bytecode = True
sys.path.insert(0, str(BUNDLE_ROOT / "tools" / "harness"))
import bundle  # noqa: E402


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def markdown_section(body, heading):
    plural = "s?" if heading.endswith("example") else ""
    heading_pattern = re.compile(rf"^## {re.escape(heading)}{plural}\s*$")
    lines = body.splitlines()
    for index, line in enumerate(lines):
        if not heading_pattern.fullmatch(line):
            continue
        section = []
        fence_char, fence_size = "", 0
        for content in lines[index + 1:]:
            fence = re.match(r"^\s*(`{3,}|~{3,})", content)
            if fence:
                delimiter = fence.group(1)
                if not fence_char:
                    fence_char, fence_size = delimiter[0], len(delimiter)
                elif delimiter[0] == fence_char and len(delimiter) >= fence_size:
                    fence_char, fence_size = "", 0
            elif not fence_char and re.match(r"^#{1,2}\s", content):
                break
            section.append(content)
        return "\n".join(section).strip()
    return ""


def fenced_blocks(section):
    return [(match.group(1).lower(), match.group(2).strip())
            for match in re.finditer(r"```([\w+-]*)\n(.*?)\n```", section, flags=re.S)]


def variant_examples(body):
    variants = re.finditer(r"^# Variant[^\n]*\n(.*?)(?=^#\s|\Z)", body, flags=re.M | re.S)
    for variant_index, match in enumerate(variants, 1):
        for block_index, (lang, code) in enumerate(fenced_blocks(match.group(1)), 1):
            labels = list(bundle.VARIANT_LABEL.finditer(code))
            for label_index, label in enumerate(labels):
                end = labels[label_index + 1].start() if label_index + 1 < len(labels) else len(code)
                snippet = code[label.start():end].strip()
                if snippet:
                    yield label.group(1).lower(), lang, snippet, f"variant-{variant_index}-{block_index}-{label.group(1).lower()}"


def case_examples(body, kind):
    section = markdown_section(body, f"{kind} example")
    for block_index, (lang, code) in enumerate(fenced_blocks(section), 1):
        if code:
            suffix = kind.lower() if block_index == 1 else f"{kind.lower()}-{block_index}"
            yield lang, code, suffix


def marked_source_files(code):
    """Split a snippet whose `// File.ext` lines represent separate source files."""
    marker = re.compile(r"^//\s+([A-Za-z0-9_.-]+\.(?:cs|ts|tsx))\s*$", re.I)
    files, target, lines = {}, None, []
    for line in code.splitlines():
        match = marker.fullmatch(line)
        if match:
            if target is not None:
                files[target] = "\n".join(lines).strip() + "\n"
            target, lines = safe_repo_path(f"src/{match.group(1)}"), []
        elif target is not None:
            lines.append(line)
    if target is not None:
        files[target] = "\n".join(lines).strip() + "\n"
    return files


def tree_source_files(code):
    """Turn an indented directory tree into changed placeholder files for layout evals."""
    files, directories = {}, []
    for line in code.splitlines():
        if not line.strip():
            continue
        spaces = len(line) - len(line.lstrip(" "))
        if spaces % 2:
            raise ValueError("evaluation tree indentation must use two spaces per level")
        level, name = spaces // 2, line.strip()
        if name.endswith("/"):
            directories = directories[:level] + [name[:-1]]
            continue
        target = safe_repo_path(pathlib.PurePosixPath(*directories[:level], name).as_posix())
        files[target] = f"// Evaluation fixture for {target}.\n"
    return files


def case_source_files(meta, lang, code):
    if bundle.unquote(meta.get("eval_split_files", "")).lower() == "true":
        files = marked_source_files(code)
        if not files:
            raise ValueError("eval_split_files needs at least one // File.ext marker")
        return files, None
    if bundle.unquote(meta.get("eval_tree", "")).lower() == "true":
        files = tree_source_files(code)
        if not files:
            raise ValueError("eval_tree needs at least one file")
        return files, None
    target = safe_repo_path(bundle.unquote(meta.get("example_file", "")) or
                            f"src/Example.{LANG_EXT.get(lang, 'txt')}")
    return {target: code + "\n"}, target


def write_source_files(repo, files):
    for target, content in files.items():
        destination = repo / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")


def safe_repo_path(value):
    path = pathlib.PurePosixPath(value)
    windows_path = pathlib.PureWindowsPath(value)
    if (not value or not path.parts or "\\" in value or path.is_absolute() or windows_path.is_absolute()
            or windows_path.drive or ".." in path.parts or path.parts[0] in {".git", ".harness"}):
        raise ValueError(f"unsafe evaluation path in example metadata: {value!r}")
    return value


def case_context_files(root, example_path, meta):
    example_id = safe_repo_path(bundle.unquote(meta.get("example_id", "")).lower())
    fixture_root = root / "examples" / "fixtures" / example_id
    files = []
    for value in bundle.as_list(meta.get("eval_context_files", "")):
        target = safe_repo_path(bundle.unquote(value))
        source = fixture_root / target
        if not source.is_file():
            raise FileNotFoundError(f"evaluation context fixture is missing: {source}")
        files.append((target, source))
    return files


def write_case_context(repo, files):
    for target, source in files:
        destination = repo / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


def from_cases(root):
    for path, meta, body in bundle.concepts(root):
        if not meta or bundle.unquote(meta.get("type", "")) != "Example":
            continue
        behavior = bundle.unquote(meta.get("eval_behavior", ""))
        # Unverified examples are evaluated but advisory: a draft cannot fail the gate. Behavior examples always gate.
        advisory = not (bundle.human_verified(meta) or behavior)
        verdict = bundle.unquote(meta.get("verdict", ""))
        if verdict not in ("violation", "compliant", "boundary"):
            continue
        rule_paths = bundle.as_list(meta.get("rule", ""))
        rule_ids = []
        for rule_path in rule_paths:
            rule_meta, _ = bundle.parse(root / rule_path.lstrip("/"))
            if rule_meta:
                rule_ids.append(bundle.unquote(rule_meta.get("rule_id", "")))
        if not rule_ids:
            continue
        rule_id = bundle.unquote(meta.get("eval_rule_id", rule_ids[0]))
        bad_rule_id = bundle.unquote(meta.get("eval_bad_rule_id", rule_id))
        pr = markdown_section(body, "PR description")
        context_files = case_context_files(root, path, meta)
        # An boundary example's bad example is what the rule normally flags; only its good side is a hard expectation.
        kinds = (("Good", "clean"),) if verdict == "boundary" else (("Bad", "find"), ("Good", "clean"))
        for kind, expect in kinds:
            for lang, code, suffix in case_examples(body, kind):
                files, target = case_source_files(meta, lang, code)
                finding = {"rule_id": bad_rule_id if expect == "find" else rule_id}
                if target:
                    finding["file"] = target
                spec = {"description": f"{path.stem}: {kind.lower()} example", "tags": ["example", kind.lower()],
                        "critical": bundle.unquote(meta.get("eval_critical", "")).lower() == "true",
                        "verified": bundle.human_verified(meta),
                        "advisory": advisory,
                        "mask_example": verdict != "boundary",
                        "example_path": path.relative_to(root).as_posix(),
                        "expect": {"must_find": [finding]}
                        if expect == "find" else {"must_not_find": [rule_id]}}
                write = lambda repo, source_files=files: write_source_files(repo, source_files)
                before = lambda repo, files=context_files: write_case_context(repo, files)
                yield f"example-{path.stem}-{suffix}", spec, before, write, pr
        for variant_kind, lang, code, suffix in variant_examples(body):
            target = safe_repo_path(f"src/Example.{LANG_EXT.get(lang, 'txt')}")
            expected_rule_id = bad_rule_id if variant_kind == "bad" else rule_id
            spec = {"description": f"{path.stem}: {suffix}", "tags": ["example", "variant", variant_kind],
                    "critical": bundle.unquote(meta.get("eval_critical", "")).lower() == "true",
                    "verified": bundle.human_verified(meta),
                    "advisory": advisory,
                    "mask_example": verdict != "boundary",
                    "example_path": path.relative_to(root).as_posix(),
                    "expect": {"must_find": [{"rule_id": expected_rule_id, "file": target}]}
                    if variant_kind == "bad" else {"must_not_find": [rule_id]}}
            write = lambda repo, t=target, c=code: ((repo / t).parent.mkdir(parents=True, exist_ok=True),
                                                    (repo / t).write_text(c + "\n", encoding="utf-8"))
            before = lambda repo, files=context_files: write_case_context(repo, files)
            yield f"example-{path.stem}-{suffix}", spec, before, write, pr

        if behavior == "rename":
            code = next(case_examples(body, "Good"), (None, None, None))[1]
            before_file = safe_repo_path(bundle.unquote(meta.get("eval_before_file", "")))
            after_file = safe_repo_path(bundle.unquote(meta.get("eval_after_file", "")))
            if code and before_file and after_file:
                def before(repo, t=before_file, c=code):
                    (repo / t).parent.mkdir(parents=True, exist_ok=True)
                    (repo / t).write_text(c + "\n", encoding="utf-8")

                def after(repo, t=after_file, c=code, old=before_file):
                    (repo / old).unlink()
                    (repo / t).parent.mkdir(parents=True, exist_ok=True)
                    (repo / t).write_text(c + "\n", encoding="utf-8")

                spec = {"description": f"{path.stem}: pure rename", "tags": ["abstention"],
                        "critical": True, "verified": bundle.human_verified(meta),
                        "advisory": advisory,
                        "mask_example": True,
                        "example_path": path.relative_to(root).as_posix(),
                        "expect": {"max_high_findings": 0}}
                yield f"example-{path.stem}-pure-rename", spec, before, after, ""


def score(spec, findings):
    expect = spec.get("expect", {})
    found, missed = [], []
    for want in expect.get("must_find", []):
        line_range = want.get("lines")
        hit = any(f["rule_id"] == want["rule_id"]
                  and (not want.get("file") or f["file"].lstrip("/") == want["file"])
                  and (not line_range or line_range[0] - LINE_TOLERANCE <= f["line"] <= line_range[1] + LINE_TOLERANCE)
                  for f in findings)
        (found if hit else missed).append(want["rule_id"])
    forbidden = set(expect.get("must_not_find", []))
    false_positives = [f["rule_id"] for f in findings if f["rule_id"] in forbidden]
    high = [f for f in findings if f["severity"] in HIGH]
    too_many = "max_high_findings" in expect and len(high) > expect["max_high_findings"]
    return {"passed": not missed and not false_positives and not too_many, "found": found, "missed": missed,
            "false_positives": false_positives, "high_findings": len(high), "too_many": too_many}


def copy_evaluation_bundle(source, destination, spec):
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__"))
    if spec.get("mask_example"):
        (destination / spec["example_path"]).unlink()
        cases_directory = destination / "examples"
        (cases_directory / "index.md").write_text(bundle.generated_index(cases_directory, destination),
                                                  encoding="utf-8")


def review_environment(args, name):
    allowed = {"codex": CODEX_CLI_ENVIRONMENT, "copilot": COPILOT_CLI_ENVIRONMENT,
               "agy": AGY_CLI_ENVIRONMENT}.get(args.engine, CLI_ENVIRONMENT)
    environment = {key: os.environ[key] for key in allowed if key in os.environ}
    environment["HARNESS_REVIEW_ENGINE"] = args.engine
    if args.engine == "replay":
        environment["HARNESS_REPLAY_FILE"] = str(pathlib.Path(args.replay_dir) / f"{name}.txt")
    if args.model:
        environment["HARNESS_REVIEW_MODEL"] = args.model
    return environment


def engine_preflight_error(args):
    if args.engine == "replay":
        return None
    cli = args.engine
    if shutil.which(cli) is None:
        return f"{cli.capitalize()} CLI was not found on PATH."
    if args.engine != "claude":
        return None
    try:
        result = subprocess.run([shutil.which("claude") or "claude", "auth", "status"], capture_output=True, text=True,
                                timeout=15, env=review_environment(args, "auth-check"))
    except FileNotFoundError:
        return "Claude CLI was not found on PATH."
    except subprocess.TimeoutExpired:
        return "Claude authentication status check timed out."

    try:
        status = json.loads(result.stdout)
    except json.JSONDecodeError:
        return f"Claude authentication status check failed (exit {result.returncode})."
    if status.get("loggedIn") is not True:
        return "Claude CLI is not authenticated. Run `claude`, enter `/login`, then retry."
    if result.returncode != 0:
        return f"Claude authentication status check failed (exit {result.returncode})."
    return None


def run_one(name, spec, before, after, pr, args):
    with tempfile.TemporaryDirectory(prefix=f"harness-eval-{name}-") as tmp:
        repo = pathlib.Path(tmp) / "repo"
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "eval@harness.invalid")
        git(repo, "config", "user.name", "harness eval")
        before(repo)
        (repo / ".gitkeep").write_text("")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "before")
        after(repo)
        git(repo, "add", "-A")
        review = pathlib.Path(tmp) / "review"
        review.mkdir()
        changed = subprocess.run(["git", "-C", str(repo), "diff", "--cached", "--name-only"],
                                 check=True, capture_output=True, text=True).stdout
        diff = subprocess.run(["git", "-C", str(repo), "diff", "--cached"], check=True, capture_output=True, text=True).stdout
        (review / "changed.txt").write_text(changed)
        (review / "diff.patch").write_text(diff)
        (review / "pr.txt").write_text(pr)
        copy_evaluation_bundle(args.bundle, repo / ".harness", spec)
        proc = subprocess.run(["bash", str(repo / ".harness/tools/review/review.sh"), str(review)], cwd=repo,
                              capture_output=True, text=True, env=review_environment(args, name))
        if proc.returncode != 0:
            return {"passed": False, "error": proc.stderr.strip()[-500:]}
        findings = json.loads((review / "findings.json").read_text())
        result = score(spec, findings)
        result["dropped"] = proc.stderr.count("dropped finding")
        if not result["passed"]:
            # Evidence for the failure (AI Evaluation Standard: preserve failed outcomes); generated test data only.
            result["raw"] = (review / "raw.txt").read_text()[:2000]
        return result


def run_scenarios(scenarios, args, thresholds):
    scenario_runs = [[] for _ in scenarios]
    tasks = []
    for index, (name, spec, before, after, pr) in enumerate(scenarios):
        repeats = thresholds["critical_repeats"] if spec.get("critical") and args.engine != "replay" else 1
        tasks.extend((index, repeat, repeats, name, spec, before, after, pr)
                     for repeat in range(1, repeats + 1))

    total = len(tasks)
    print(f"Running {len(scenarios)} scenarios ({total} eval runs) with {args.jobs} workers.", flush=True)
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        pending = {
            executor.submit(run_one, name, spec, before, after, pr, args): (index, repeat, repeats, name)
            for index, repeat, repeats, name, spec, before, after, pr in tasks
        }
        for completed, future in enumerate(as_completed(pending), 1):
            index, repeat, repeats, name = pending[future]
            result = future.result()
            scenario_runs[index].append(result)
            status = "pass" if result["passed"] else "FAIL"
            detail = result.get("error")
            if not result["passed"] and not detail:
                problems = []
                if result.get("missed"):
                    problems.append(f"missed {result['missed']}")
                if result.get("false_positives"):
                    problems.append(f"false positives {result['false_positives']}")
                if result.get("too_many"):
                    problems.append(f"too many high-severity findings ({result.get('high_findings', 0)})")
                detail = ", ".join(problems) or "score did not pass"
            detail = f" ({detail})" if detail else ""
            print(f"{status} [{completed}/{total} runs]  {name} ({repeat}/{repeats}){detail}", flush=True)

    results = []
    for (name, spec, *_), runs in zip(scenarios, scenario_runs):
        result = next((run for run in runs if not run["passed"]), runs[0])
        result.update(name=name, tags=spec.get("tags", []), critical=spec.get("critical", False),
                      advisory=spec.get("advisory", False),
                      runs=len(runs), runs_passed=sum(run["passed"] for run in runs))
        results.append(result)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--engine", default="claude", choices=["claude", "codex", "copilot", "agy", "replay"])
    parser.add_argument("--replay-dir")
    parser.add_argument("--model", help="model to pin, recorded in the result")
    parser.add_argument("--only", action="append", help="run only this scenario (repeatable)")
    parser.add_argument("--jobs", type=int, default=2, help="maximum concurrent eval runs (default: 2, max: 8)")
    parser.add_argument("--out", type=pathlib.Path,
                        default=pathlib.Path(tempfile.gettempdir()) / "teamvalue-harness-evals")
    parser.add_argument("--bundle", type=pathlib.Path, default=DEFAULT_BUNDLE, help="bundle to review with and take examples from")
    parser.add_argument("--thresholds", type=pathlib.Path, default=HERE / "thresholds.json")
    args = parser.parse_args()
    if not 1 <= args.jobs <= 8:
        parser.error("--jobs must be between 1 and 8")
    args.out = args.out.resolve()

    preflight_error = engine_preflight_error(args)
    if preflight_error:
        print(f"review eval: {preflight_error}", file=sys.stderr)
        return 2

    thresholds = json.loads(args.thresholds.read_text(encoding="utf-8"))
    scenarios = [s for s in from_cases(args.bundle)
                 if not args.only or s[0] in args.only]
    results = run_scenarios(scenarios, args, thresholds)

    advisory_failed = [r["name"] for r in results if r["advisory"] and not r["passed"]]
    advisory_total = sum(r["advisory"] for r in results)
    scenarios = [s for s in scenarios if not s[1].get("advisory")]
    gated = [r for r in results if not r["advisory"]]
    total = len(gated)
    passed = sum(r["passed"] for r in gated)
    critical_failures = [r["name"] for r in gated if r["critical"] and not r["passed"]]
    pass_rate = passed / total if total else 0.0
    partial = bool(args.only)
    # A partial run (--only) is for development; only a full run can pass the minimum scenario count.
    counted = sum(1 for _, spec, *_ in scenarios if True)
    gate = (not critical_failures and pass_rate >= thresholds["min_pass_rate"]
            and (bool(args.only) or counted >= thresholds["min_scenarios"]))

    commit = subprocess.run(["git", "-C", str(BUNDLE_ROOT), "describe", "--always", "--dirty"], capture_output=True, text=True).stdout.strip()
    engine_cli = None if args.engine == "replay" else args.engine
    engine_version = subprocess.run([shutil.which(engine_cli) or engine_cli, "--version"], capture_output=True, text=True).stdout.strip() \
        if engine_cli else "replay"
    record = {"harness": commit, "engine": args.engine, "engine_version": engine_version, "model": args.model or "default",
              "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
              "thresholds": thresholds, "summary": {"scenarios": total, "passed": passed, "pass_rate": round(pass_rate, 3),
                                                    "critical_failures": critical_failures, "partial": partial,
                                                    "advisory": {"scenarios": advisory_total, "failed": advisory_failed},
                                                    "gate": "pass" if gate else "fail"},
              "scenarios": results}
    if args.engine != "replay":
        args.out.mkdir(parents=True, exist_ok=True)
        out = args.out / f"{record['at'][:19].replace(':', '')}-{commit}.json"   # one file per run; failures are kept
        out.write_text(json.dumps(record, indent=2) + "\n")
        print(f"recorded {out}")
        # Evidence for a harness version: only a full run on a clean commit, summary only (raw output stays local).
        if not partial and not commit.endswith("-dirty"):
            line = {k: record[k] for k in ("harness", "engine_version", "model", "at")}
            line.update(record["summary"], failed=[r["name"] for r in gated if not r["passed"]])
            with (HERE / "history.jsonl").open("a", encoding="utf-8") as history:
                history.write(json.dumps(line) + "\n")
            print("appended harness/tools/review/history.jsonl; commit it with the harness change")
    print(f"{passed}/{total} passed, critical failures: {critical_failures or 'none'}, gate: {record['summary']['gate']}")
    print(f"advisory (drafts, not gating): {advisory_total - len(advisory_failed)}/{advisory_total} passed"
          + (f", failed: {advisory_failed}" if advisory_failed else ""))
    return 0 if gate else 1


if __name__ == "__main__":
    sys.exit(main())
