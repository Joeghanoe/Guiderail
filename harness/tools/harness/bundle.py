#!/usr/bin/env python3
"""Work with the harness bundle (OKF v0.2 plus the harness's own conventions).

Commands:
  index              regenerate index.md in every directory except the bundle root
  check              OKF conformance, harness conventions, and index files up to date
  select             read changed paths on stdin, print the rules and examples that apply (JSON)
  findings <file>    validate a reviewer's JSON findings; print the valid ones, report the dropped ones
  check-example <file>  validate one draft example outside the bundle (e.g. harness-feedback/x.md) against it
  submit-feedback    prepare a local branch/worktree with a validated feedback example staged for review
  privacy-check      fail if private feedback or raw eval artifacts are present in the checkout
  budget             fail if the always-loaded context (AGENTS.base.md, index.md) outgrew context-budget.json

The bundle root is the directory above this script's directory, or --root <dir>.
Frontmatter is parsed line by line on purpose: no PyYAML needed on a build agent. Lists such as
applies_to are written as inline JSON-compatible lists (["a", "b"]), which `check` enforces.

Example:
  git diff --name-only origin/main...HEAD | python3 .harness/tools/harness/bundle.py select
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

INDEX = "index.md"
RESERVED = {INDEX, "log.md"}
TYPES_IN_DIR = {"principles": "Principle", "rules": "Rule", "examples": "Example", "playbooks": "Playbook", "gates": "Gate"}
SEVERITIES = ["blocker", "major", "minor", "nit"]
VERDICTS = {"violation", "compliant", "boundary", "rejected", "open", "automation-candidate"}
CONFIDENCE = {"high", "medium", "low"}
NEEDS_CODE = {"violation", "compliant", "boundary"}
EXAMPLE = r"^## {} examples?\s*\n+```[\w+-]*\n(?!<code snippet>)\S"
NOT_CONCEPTS = {"tools", "hooks", "templates"}
LINK = re.compile(r"\]\((/[^)\s#]+)")


def parse(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return None, text
    meta = {"_frontmatter": text[4:end]}
    for line in text[4:end].splitlines():
        key, sep, value = line.partition(":")
        if sep and re.fullmatch(r"[A-Za-z_][\w-]*", key):
            meta[key] = value.strip()
    return meta, text[end + 5:]


def unquote(value):
    value = value.split(" #", 1)[0].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def as_list(value):
    """Inline lists: ["a", "b"] (JSON) or [a, b] (bare words). A single value becomes a list of one."""
    value = value.split(" #", 1)[0].strip()
    if not value:
        return []
    if value.startswith("["):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return [unquote(v.strip()) for v in value[1:-1].split(",") if v.strip()]
    return [unquote(value)]


def concepts(root):
    for path in sorted(root.rglob("*.md")):
        if path.name in RESERVED or set(path.relative_to(root).parts) & NOT_CONCEPTS:
            continue
        meta, body = parse(path)
        yield path, meta, body


def glob_to_regex(pattern):
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile("^" + out + "$")


def is_stale(meta, now):
    """OKF stale_after: a concept is stale when now >= stale_after."""
    value = unquote(meta.get("stale_after", "")).replace("Z", "+00:00")
    try:
        return now >= datetime.datetime.fromisoformat(value)
    except ValueError:
        return False


def human_verified(meta):
    return "human:" in meta.get("verified", "")


def generated_index(directory, root):
    lines = []
    heading = TYPES_IN_DIR.get(directory.relative_to(root).parts[0], "Concept") + "s"
    subdirs = sorted(d for d in directory.iterdir() if d.is_dir() and any(d.rglob("*.md")))
    files = sorted(p for p in directory.glob("*.md") if p.name not in RESERVED)
    if subdirs:
        lines.append("# Folders\n")
        for d in subdirs:
            count = sum(1 for p in d.rglob("*.md") if p.name not in RESERVED)
            lines.append(f"* [{d.name}]({d.name}/) - {count} concepts")
        lines.append("")
    if files:
        lines.append(f"# {heading}\n")
        for p in files:
            meta, _ = parse(p)
            meta = meta or {}
            title = unquote(meta.get("title", p.stem))
            extra = ""
            if meta.get("verdict"):
                trust = "human-reviewed" if human_verified(meta) else "unverified"
                extra = f" ({unquote(meta['verdict'])}, {trust})"
            lines.append(f"* [{title}]({p.name}) - {unquote(meta.get('description', ''))}{extra}")
        lines.append("")
    if not lines:
        lines = [f"# {heading}\n", "None yet.", ""]
    return "\n".join(lines)


def index_dirs(root):
    for d in sorted([root, *[p for p in root.rglob("*") if p.is_dir()]]):
        if d == root or set(d.relative_to(root).parts) & NOT_CONCEPTS:
            continue
        yield d


def cmd_index(root, _args):
    for d in index_dirs(root):
        (d / INDEX).write_text(generated_index(d, root), encoding="utf-8")
        print((d.relative_to(root) / INDEX).as_posix())
    return 0


def check_ids(rel, meta, kind, ids):
    id_key = {"Principle": "principle_id", "Rule": "rule_id", "Example": "example_id"}.get(kind)
    if not id_key:
        return []
    cid = unquote(meta.get(id_key, ""))
    if not cid:
        return [f"{rel}: no {id_key}"]
    if cid in ids:
        return [f"{rel}: {id_key} {cid} also used in {ids[cid]}"]
    ids[cid] = rel
    return []


def check_rule(rel, meta):
    errors = []
    if unquote(meta.get("severity", "")) not in SEVERITIES:
        errors.append(f"{rel}: severity must be one of {SEVERITIES}")
    if not meta.get("enforced_by"):
        errors.append(f"{rel}: no enforced_by")
    if not meta.get("principle"):
        errors.append(f"{rel}: no principle")
    try:
        globs = json.loads(meta.get("applies_to", ""))
        valid = bool(globs) and all(isinstance(g, str) for g in globs)
    except ValueError:
        valid = False
    if not valid:
        errors.append(f"{rel}: applies_to must be a JSON list of globs")
    return errors


def project_terms(root, extra=None):
    names = []
    for source in [root / "templates" / "project-terms.txt", *([extra] if extra else [])]:
        if source and pathlib.Path(source).is_file():
            names += [l.strip() for l in pathlib.Path(source).read_text(encoding="utf-8").splitlines()
                      if l.strip() and not l.startswith("#")]
    return names


def check_agnostic(rel, meta, body, terms):
    text = " ".join([meta.get("title", ""), meta.get("description", ""), body])
    hits = sorted({t for t in terms if re.search(rf"(?<![\w.]){re.escape(t)}(?![\w])", text, flags=re.I)})
    return [f"{rel}: project-specific name(s) {hits}; generalize the example"] if hits else []


# A "Good" / "Bad" comment starting a line in a variant code block; the colon is optional.
VARIANT_LABEL = re.compile(r"(?m)^\s*(?://|#|/\*|\*)\s*(Good|Bad)\b:?", re.I)


def check_variants(rel, body):
    errors = []
    for index, match in enumerate(re.finditer(r"^# Variant[^\n]*\n(.*?)(?=^#\s|\Z)", body, flags=re.M | re.S), 1):
        blocks = re.findall(r"```[\w+-]*\n(.*?)\n```", match.group(1), flags=re.S)
        if blocks and not any(VARIANT_LABEL.search(block) for block in blocks):
            errors.append(f"{rel}: variant {index} has code but no 'Good' / 'Bad' comment markers to evaluate")
    return errors


def check_case(rel, meta, body):
    errors = check_variants(rel, body)
    verdict = unquote(meta.get("verdict", ""))
    if verdict not in VERDICTS:
        errors.append(f"{rel}: verdict must be one of {sorted(VERDICTS)}")
    if not meta.get("rule"):
        errors.append(f"{rel}: no rule")
    if verdict == "boundary":
        if not meta.get("owner", "").startswith("human:"):
            errors.append(f"{rel}: a boundary example needs owner: human:<id> (who accepted the deviation)")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T[\d:]+(Z|[+-]\d{2}:\d{2})", unquote(meta.get("stale_after", ""))):
            errors.append(f"{rel}: a boundary example needs stale_after (ISO 8601 with offset)")
        if not re.search(r"^\s*-\s*id:\s*requirement\s*$", meta["_frontmatter"], flags=re.M):
            errors.append(f"{rel}: a boundary example needs a sources entry with id: requirement")
    if verdict in NEEDS_CODE:
        errors += [f"{rel}: a {verdict} example needs a '## {kind} example' heading followed by a code block"
                   for kind in ("Good", "Bad") if not re.search(EXAMPLE.format(kind), body, flags=re.M)]
    behavior = unquote(meta.get("eval_behavior", ""))
    if behavior and behavior not in {"adversarial", "rename"}:
        errors.append(f"{rel}: eval_behavior must be 'adversarial' or 'rename'")
    if behavior == "adversarial" and not re.search(
            r"^## PR description\s*\n\S", body, flags=re.M):
        errors.append(f"{rel}: an adversarial evaluation needs a non-empty '## PR description' section")
    if behavior == "rename":
        before = unquote(meta.get("eval_before_file", ""))
        after = unquote(meta.get("eval_after_file", ""))
        if not before or not after or before == after:
            errors.append(f"{rel}: a rename evaluation needs distinct eval_before_file and eval_after_file paths")
    eval_critical = unquote(meta.get("eval_critical", ""))
    if eval_critical and eval_critical.lower() not in {"true", "false"}:
        errors.append(f"{rel}: eval_critical must be true or false")
    for key in ("eval_split_files", "eval_tree"):
        value = unquote(meta.get(key, ""))
        if value and value.lower() not in {"true", "false"}:
            errors.append(f"{rel}: {key} must be true or false")
    for key in ("example_file", "eval_before_file", "eval_after_file"):
        value = unquote(meta.get(key, ""))
        if value and not safe_repo_path(value):
            errors.append(f"{rel}: {key} must be a safe relative source path")
    return errors


def safe_repo_path(value):
    path = pathlib.PurePosixPath(value)
    windows_path = pathlib.PureWindowsPath(value)
    return bool(value and path.parts and "\\" not in value and not path.is_absolute()
                and not windows_path.is_absolute() and not windows_path.drive and ".." not in path.parts
                and path.parts[0] not in {".git", ".harness"})


def check_links(root, rel, meta, body):
    targets = [(key, t) for key in ("principle", "rule") for t in as_list(meta.get(key, ""))]
    targets += [("link", t) for t in LINK.findall(body)]
    errors = []
    for key, target in targets:
        if not safe_repo_path(target.lstrip("/")):
            errors.append(f"{rel}: {key} {target} is not a safe bundle-relative path")
        elif not (root / target.lstrip("/")).exists():
            errors.append(f"{rel}: {key} {target} does not exist")
    return errors


def check_concept(root, path, meta, body, ids):
    rel = "/" + path.relative_to(root).as_posix()
    if meta is None:
        return [f"{rel}: no frontmatter (OKF requires it)"]
    kind = unquote(meta.get("type", ""))
    errors = [] if kind else [f"{rel}: no type (OKF requires it)"]
    errors += [f"{rel}: no {key}" for key in ("title", "description") if not meta.get(key)]
    top = path.relative_to(root).parts[0]
    if kind == "Principle" and "resource:" not in meta["_frontmatter"]:
        errors.append(f"{rel}: a principle points to its authority in sources")
    if kind == "Gate":
        errors += [f"{rel}: no {key}" for key in ("tool", "owner") if not meta.get(key)]
    if top in TYPES_IN_DIR and kind != TYPES_IN_DIR[top]:
        errors.append(f"{rel}: type '{kind}' in {top}/ should be '{TYPES_IN_DIR[top]}'")
    errors += check_ids(rel, meta, kind, ids)
    if kind == "Rule":
        errors += check_rule(rel, meta)
    elif kind == "Example":
        errors += check_case(rel, meta, body)
        errors += check_agnostic(rel, meta, body, project_terms(root))
        if meta.get("eval_rule_id"):
            available = set()
            for rule_path in as_list(meta.get("rule", "")):
                if safe_repo_path(rule_path.lstrip("/")):
                    rule_meta, _ = parse(root / rule_path.lstrip("/"))
                    if rule_meta and unquote(rule_meta.get("rule_id", "")):
                        available.add(unquote(rule_meta["rule_id"]))
            if unquote(meta["eval_rule_id"]) not in available:
                errors.append(f"{rel}: eval_rule_id must name one of the example's rules")
    return errors + check_links(root, rel, meta, body)


def check_indexes(root):
    errors = []
    for d in index_dirs(root):
        index = d / INDEX
        if not index.is_file() or index.read_text(encoding="utf-8") != generated_index(d, root):
            errors.append(f"/{index.relative_to(root).as_posix()}: out of date, run bundle.py index")
    root_index = (root / INDEX).read_text(encoding="utf-8") if (root / INDEX).is_file() else ""
    errors += [f"/index.md: does not link {top}/" for top in TYPES_IN_DIR
               if (root / top).is_dir() and f"]({top}/)" not in root_index]
    return errors


def cmd_check(root, _args):
    ids = {}
    errors = [e for path, meta, body in concepts(root) for e in check_concept(root, path, meta, body, ids)]
    errors += check_indexes(root)
    for e in errors:
        print(e, file=sys.stderr)
    print(f"bundle check: {len(errors)} problem(s)")
    return 1 if errors else 0


BUDGET_FILE = "tools/harness/context-budget.json"


def measure_context(root):
    """Bytes every agent loads before it opens anything: the base instructions and the bundle index."""
    return {"agentsBaseBytes": (root.parent / "AGENTS.base.md").stat().st_size,
            "indexBytes": (root / INDEX).stat().st_size}


def cmd_budget(root, args):
    path = root / BUDGET_FILE
    measured = measure_context(root)
    if args.update:
        path.write_text(json.dumps(measured, indent=2) + "\n", encoding="utf-8")
        print(f"budget: recorded {measured}")
        return 0
    recorded = json.loads(path.read_text(encoding="utf-8"))
    errors = [f"{key}: {value} bytes, budget {recorded.get(key)}; cut the added text, or run "
              "`bundle.py budget --update` and justify the growth in the commit message"
              for key, value in measured.items() if value > recorded.get(key, 0)]
    if args.baseline:
        base = json.loads(pathlib.Path(args.baseline).read_text(encoding="utf-8"))
        errors += [f"{key}: budget raised from {base[key]} to {value} compared with the base branch"
                   for key, value in recorded.items() if key in base and value > base[key]]
    for e in errors:
        print(e, file=sys.stderr)
    print(f"context budget: {measured}, {len(errors)} problem(s)")
    return 1 if errors else 0


def cmd_privacy_check(root, _args):
    repository = root.parent
    forbidden = (repository / "feedback" / "mined", repository / "evals" / "results")
    files = []
    for directory in forbidden:
        if directory.is_symlink():
            files.append(directory)
        elif directory.exists():
            files.extend(path for path in directory.rglob("*") if path.is_file() or path.is_symlink())
    tracked = subprocess.run(["git", "-C", str(repository), "ls-files", "--", "*.pyc", "*__pycache__*"],
                             capture_output=True, text=True, check=False).stdout.split()
    files.extend(repository / name for name in tracked)
    files.sort()
    for path in files:
        print(f"private artifact must not be in the checkout: {path.relative_to(repository)}", file=sys.stderr)
    print(f"privacy check: {len(files)} private artifact(s)")
    return 1 if files else 0


def cmd_check_example(root, args):
    path = pathlib.Path(args.file)
    meta, body = parse(path)
    if meta is None:
        errors = [f"{path}: no frontmatter"]
    elif unquote(meta.get("type", "")) != "Example":
        errors = [f"{path}: type must be Example"]
    else:
        errors = [f"{path}: no {key}" for key in ("title", "description") if not meta.get(key)]
        errors += check_case(str(path), meta, body)
        errors += check_links(root, str(path), meta, body)
        repo = pathlib.Path.cwd().name
        errors += check_agnostic(str(path), meta, body, project_terms(root, args.terms) + [repo])
    for e in errors:
        print(e, file=sys.stderr)
    print(f"example check: {len(errors)} problem(s)")
    return 1 if errors else 0


def cmd_submit_feedback(root, args):
    repository = root.parent.resolve()
    source = pathlib.Path(args.file).resolve()
    feedback = (repository / "feedback").resolve()
    try:
        source.relative_to(feedback)
    except ValueError:
        print("submit-feedback: input must be a Markdown draft under feedback/", file=sys.stderr)
        return 1
    if source.suffix != ".md":
        print("submit-feedback: input must be a Markdown draft under feedback/", file=sys.stderr)
        return 1

    meta, body = parse(source)
    if not meta or unquote(meta.get("status", "")) != "draft" or meta.get("verified"):
        print("submit-feedback: input must have status: draft and no verified metadata", file=sys.stderr)
        return 1
    errors = [f"{source}: no {key}" for key in ("title", "description") if not meta.get(key)]
    errors += check_case(str(source), meta, body) + check_links(root, str(source), meta, body)
    errors += check_agnostic(str(source), meta, body, project_terms(root))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"example check: {len(errors)} problem(s)")
        return 1

    example_id = unquote(meta.get("example_id", ""))
    if not re.fullmatch(r"E-\d{3,}", example_id):
        print("submit-feedback: draft needs an example_id such as E-020", file=sys.stderr)
        return 1
    if any(unquote(existing.get("example_id", "")) == example_id
           for _, existing, _ in concepts(root) if existing):
        print(f"submit-feedback: example_id {example_id} already exists in the bundle", file=sys.stderr)
        return 1

    slug = re.sub(r"[^a-z0-9]+", "-", f"{example_id}-{source.stem}".lower()).strip("-")[:100].rstrip("-")
    branch = f"feedback/{slug}"
    destination = pathlib.Path(args.worktree_dir or pathlib.Path(os.getenv("GOLDEN_PATH_HOME") or pathlib.Path.home() / ".golden-path-harness") / "workspaces" / "feedback" / slug)
    destination = destination.expanduser()
    if destination.exists() or destination.is_symlink():
        print(f"submit-feedback: worktree path already exists: {destination}", file=sys.stderr)
        return 1
    destination = destination.resolve()
    if (repository / "harness" / "examples" / source.name).exists():
        print(f"submit-feedback: example file {source.name} already exists in the bundle", file=sys.stderr)
        return 1

    top_level = subprocess.run(["git", "-C", str(repository), "rev-parse", "--show-toplevel"],
                               capture_output=True, text=True, check=False)
    if top_level.returncode or pathlib.Path(top_level.stdout.strip()).resolve() != repository:
        print("submit-feedback: feedback must be submitted from a Git checkout of the harness", file=sys.stderr)
        if top_level.stderr:
            print(top_level.stderr, file=sys.stderr, end="")
        return 1

    destination.parent.mkdir(parents=True, exist_ok=True)
    created = subprocess.run(["git", "-C", str(repository), "worktree", "add", "-b", branch,
                              str(destination), "HEAD"], capture_output=True, text=True, check=False)
    if created.returncode:
        print("submit-feedback: could not create the local branch/worktree", file=sys.stderr)
        if created.stderr:
            print(created.stderr, file=sys.stderr, end="")
        return created.returncode

    target = destination / "harness" / "examples" / source.name
    shutil.copy2(source, target)
    index = subprocess.run([sys.executable, str(destination / "harness" / "tools" / "harness" / "bundle.py"),
                            "index"], cwd=destination, capture_output=True, text=True, check=False)
    if index.returncode:
        print("submit-feedback: worktree created but bundle index refresh failed", file=sys.stderr)
        if index.stderr:
            print(index.stderr, file=sys.stderr, end="")
        return index.returncode
    staged = subprocess.run(["git", "-C", str(destination), "add", "--",
                             f"harness/examples/{source.name}", "harness/examples/index.md"],
                            capture_output=True, text=True, check=False)
    if staged.returncode:
        print(f"submit-feedback: worktree created at {destination}, but staging failed", file=sys.stderr)
        if staged.stderr:
            print(staged.stderr, file=sys.stderr, end="")
        return staged.returncode
    print(f"Prepared {branch} at {destination}; the example and index are staged.")
    print("Review the staged diff, then commit, push, and open the PR yourself.")
    return 0


def cmd_select(root, _args):
    changed = [line.strip() for line in sys.stdin if line.strip()]
    rules, examples = {}, []
    for path, meta, _ in concepts(root):
        if not meta:
            continue
        kind = unquote(meta.get("type", ""))
        rel = "/" + path.relative_to(root).as_posix()
        if kind == "Rule":
            globs = [glob_to_regex(g) for g in json.loads(meta.get("applies_to", "[]"))]
            if any(g.match(f) for g in globs for f in changed):
                rules[rel] = unquote(meta.get("rule_id", ""))
        elif kind == "Example":
            examples.append((rel, meta))
    now = datetime.datetime.now(datetime.timezone.utc)
    relevant = [(rel, m) for rel, m in examples if set(as_list(m.get("rule", ""))) & set(rules)]
    stale = [rel for rel, m in relevant if is_stale(m, now)]
    precedent = [rel for rel, m in relevant if human_verified(m) and rel not in stale]
    hints = [rel for rel, m in relevant if not human_verified(m) and rel not in stale]
    print(json.dumps({"rules": rules, "precedent": precedent, "hints": hints, "stale": stale}, indent=2))
    return 0


def finding_problem(f, known):
    if not isinstance(f, dict):
        return "not an object"
    if f.get("rule_id") not in known:
        return f"unknown rule_id {f.get('rule_id')!r}"
    if not f.get("file") or not isinstance(f.get("line"), int) or f["line"] < 1:
        return "no file or line"
    if not f.get("evidence"):
        return "no evidence"
    if f.get("confidence") not in CONFIDENCE:
        return "confidence must be high, medium or low"
    return None


def anchor(finding, repo):
    """Put the finding on the line its evidence is on; models miscount lines, the quoted code does not move."""
    path = repo / finding["file"].lstrip("/")
    if not path.is_file():
        return "file not in the repo"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    needle = " ".join(finding["evidence"].split())[:80]
    hits = [i for i, line in enumerate(lines, 1) if needle and needle in " ".join(line.split())]
    if hits:
        finding["line"] = min(hits, key=lambda i: abs(i - finding["line"]))
        finding["anchored"] = True
    else:
        finding["line"] = min(finding["line"], max(len(lines), 1))
        finding["anchored"] = False
    return None


def cmd_findings(root, args):
    raw = pathlib.Path(args.file).read_text(encoding="utf-8").strip()
    fenced = re.search(r"```(?:json)?\s*(\[.*\])\s*```", raw, flags=re.S)
    raw = fenced.group(1) if fenced else raw[raw.find("["): raw.rfind("]") + 1]
    try:
        findings = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"findings: not a JSON array ({e})", file=sys.stderr)
        return 1
    known = {}
    for _, meta, _ in concepts(root):
        if meta and unquote(meta.get("type", "")) == "Rule":
            known[unquote(meta["rule_id"])] = unquote(meta.get("severity", "major"))
    valid = []
    for i, f in enumerate(findings):
        problem = finding_problem(f, known)
        if problem:
            print(f"dropped finding {i}: {problem}", file=sys.stderr)
            continue
        if f.get("severity") not in SEVERITIES:
            f["severity"] = known[f["rule_id"]]
        if args.repo and (problem := anchor(f, pathlib.Path(args.repo))):
            print(f"dropped finding {i}: {problem}", file=sys.stderr)
            continue
        valid.append(f)
    valid.sort(key=lambda f: (SEVERITIES.index(f["severity"]), f["file"], f["line"]))
    print(json.dumps(valid, indent=2))
    print(f"findings: {len(valid)} valid, {len(findings) - len(valid)} dropped", file=sys.stderr)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parent.parent.parent)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("index")
    sub.add_parser("check")
    sub.add_parser("privacy-check")
    budget = sub.add_parser("budget")
    budget.add_argument("--update", action="store_true", help="record the measured sizes as the new budget")
    budget.add_argument("--baseline", help="budget file from the base branch; fail if this one raises a value")
    sub.add_parser("select")
    findings = sub.add_parser("findings")
    findings.add_argument("file")
    findings.add_argument("--repo", help="repo root: drop findings on missing files, anchor lines on the evidence")
    case = sub.add_parser("check-example")
    case.add_argument("file")
    case.add_argument("--terms", help="file with more project-specific names, one per line")
    submit = sub.add_parser("submit-feedback")
    submit.add_argument("file")
    submit.add_argument("--worktree-dir", type=pathlib.Path, help="local destination for the submission worktree")
    args = parser.parse_args()
    handler = {"index": cmd_index, "check": cmd_check, "privacy-check": cmd_privacy_check, "budget": cmd_budget,
               "select": cmd_select, "findings": cmd_findings, "check-example": cmd_check_example,
               "submit-feedback": cmd_submit_feedback}
    return handler[args.command](args.root.resolve(), args)


if __name__ == "__main__":
    sys.exit(main())
