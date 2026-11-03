#!/usr/bin/env python3
"""Static design gate for a new repo or service (DEL.4, T.1, CODE.8, OBS.3, T.3).

Reads files only; never builds or runs the repo's code, never follows symlinks. Each check names the rule it
stands for and says what it saw. These are structural proofs that the design exists, is filled in and shapes
the code, not a judgement of quality: a reviewer still reads the documents.
Profiles: `generic` (any new repo); `service` (a service that runs operations and reports them: adds the CODE.8
source/store roles and the OBS.3 contract); `web-app` (an HTTP application that talks to other systems: adds ports for
what it talks to, whatever they are called, and an error-code catalogue plus a health endpoint, without asking for run
events). Exit 0 when every check passes, 1 otherwise.
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

SKIP = {"bin", "obj", ".git", ".harness", "node_modules"}
MAX_BYTES = 512 * 1024
DESIGN_TOPICS = {
    "scope": r"scope|out of scope|non-goals?",
    "components": r"component|architecture|building blocks",
    "layout": r"layout|stor(ed|age)|data flow",
    "failure": r"fail|error|partial",
    "observability": r"observab|telemetry|events?|report|alert|health",
    "retention": r"retention|lifecycle",
    "decisions": r"decision|adr",
}
BASE_MARKER = "tvh-loaded"
REPO_AGENTS_TOPICS = {"layout": r"^#+\s.*layout", "verify": r"^#+\s.*verif", "decisions": r"^#+\s.*decision"}


def files(root, suffixes=None):
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if SKIP & set(rel.parts) or path.is_symlink() or not path.is_file():
            continue
        if suffixes and path.suffix not in suffixes:
            continue
        yield rel, path


def text(path):
    try:
        if path.stat().st_size > MAX_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def headings(markdown):
    return [m.group(1).strip().lower() for m in re.finditer(r"^#{1,4}\s+(.*)$", markdown, re.M)]


PLACEHOLDER = re.compile(r"<[^<>\n]*\s[^<>\n]*>|\bTODO\b")


def unfilled(body):
    return PLACEHOLDER.findall(body)[:3]


def check(check_id, rule, ok, detail):
    return {"id": check_id, "rule": rule, "status": "pass" if ok else "fail", "detail": detail}


def design_document(root):
    path = root / "docs" / "solution-design.md"
    body = text(path) if path.is_file() and not path.is_symlink() else ""
    found = [name for name, pattern in DESIGN_TOPICS.items() if re.search(pattern, body, re.I)]
    left = unfilled(body)
    return check("D01", "DEL.4", len(found) >= 6 and len(headings(body)) >= 5 and len(body) > 1500 and not left,
                 f"docs/solution-design.md: {len(body)} chars, {len(headings(body))} headings, "
                 f"topics mentioned {sorted(found)} of {sorted(DESIGN_TOPICS)}; template prompts left: {left or 'none'}")


def adrs(root, minimum):
    folder = root / "docs" / "adr"
    records = [(rel, text(p)) for rel, p in files(root) if rel.parent == pathlib.Path("docs/adr") and rel.suffix == ".md"]
    real = [rel.name for rel, body in records
            if re.search(r"decision", body, re.I) and re.search(r"consequence|why|context", body, re.I) and len(body) > 400]
    return check("D02", "DEL.4", len(real) >= minimum,
                 f"{len(real)} ADR(s) with context, decision and consequences in {folder.relative_to(root)}: {real[:6]}")


def repo_agents(root):
    path = root / "AGENTS.md"
    body = text(path) if path.is_file() and not path.is_symlink() else ""
    topics = [n for n, p in REPO_AGENTS_TOPICS.items() if re.search(p, body, re.I | re.M)]
    own = BASE_MARKER not in body and len(body) > 800
    left = unfilled(body)
    kind = "the repo's own" if own else "the base copy, or missing or thin"
    return check("D03", "DEL.4", own and len(topics) >= 3 and not left,
                 f"AGENTS.md is {kind}; sections {sorted(topics)}; template prompts left: {left or 'none'}")


def project_verify(root):
    """The project's quick verify, kept outside the repo (tools/code/project-verify.sh)."""
    script = pathlib.Path(__file__).resolve().parents[1] / "code" / "project-verify.sh"
    try:
        out = subprocess.run(["bash", str(script), "path", str(root)], capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    path = pathlib.Path(out.stdout.strip()) if out.returncode == 0 and out.stdout.strip() else None
    return path if path and path.is_file() and not path.is_symlink() else None


def verify_command(root):
    """T.1: format, warnings-as-errors build and tests run somewhere: CI is the authority, the per-project verify is the quick copy."""
    def runs_all(body):
        return bool(body) and "dotnet format" in body and "-warnaserror" in body.lower() and "dotnet test" in body

    where = []
    repo_verify = root / "scripts" / "verify.sh"
    if repo_verify.is_file() and not repo_verify.is_symlink() and runs_all(text(repo_verify)):
        where.append("scripts/verify.sh")
    local = project_verify(root)
    if local and runs_all(text(local)):
        where.append("the project verify")
    ci_files = [*root.glob("azure-pipelines*.yml"), *root.glob(".github/workflows/*.y*ml"), *root.glob("pipelines/**/*.yml")]
    if any(runs_all(text(f)) for f in ci_files if f.is_file() and not f.is_symlink()):
        where.append("CI")
    return check("D04", "T.1", bool(where),
                 f"format, warnings-as-errors build and tests run in {', '.join(where)}" if where
                 else "no scripts/verify.sh, project verify or CI pipeline runs format, warnings-as-errors build and tests")


def composition_root(root):
    program = [(rel, text(p)) for rel, p in files(root, {".cs"}) if rel.name == "Program.cs" and "tests" not in rel.parts]
    registrations = sum(len(re.findall(r"\.Add(Singleton|Scoped|Transient)\b|\.Configure<|\.AddOptions", b)) for _, b in program)
    return check("D05", "CODE.8", registrations >= 4, f"Program.cs makes {registrations} container registrations")


def interfaces(root):
    names = {}
    for rel, path in files(root, {".cs"}):
        if "tests" in rel.parts:
            continue
        for m in re.finditer(r"\binterface\s+(I[A-Z]\w+)", text(path)):
            names[m.group(1)] = rel.as_posix()
    roles = {"store": r"Store|Sink|Storage|Repository", "clock": r"Clock|TimeProvider", "source": r"Source|Provider|Reader",
             "events": r"Event(Sink|Writer|Publisher|Emitter)|Telemetry|Reporter"}
    covered = {r for r, p in roles.items() if any(re.search(p, n) for n in names)}
    uses_time_provider = any("TimeProvider" in text(p) for _, p in files(root, {".cs"}))
    ok = len(names) >= 4 and ({"store", "source", "events"} <= covered) and ("clock" in covered or uses_time_provider)
    return check("D06", "CODE.8", ok, f"{len(names)} interfaces {sorted(names)[:10]}; roles covered {sorted(covered)}"
                 f"{' + TimeProvider' if uses_time_provider else ''}")


def ports(root):
    """CODE.8 for an application: every system it talks to sits behind an interface that something implements.
    The roles are not named (a web app has a Directory, a Gateway, a Renderer, not a Source and a Sink)."""
    sources = [(rel, text(p)) for rel, p in files(root, {".cs"}) if "tests" not in rel.parts]
    names = {m.group(1) for _, body in sources for m in re.finditer(r"\binterface\s+(I[A-Z]\w+)", body)}
    implemented = {n for n in names for _, body in sources
                   if re.search(r"class\s+\w+[^{;]*?:\s*[^{;]*\b" + re.escape(n) + r"\b", body)}
    uses_time_provider = any("TimeProvider" in body or "IClock" in body for _, body in sources)
    ok = len(names) >= 4 and len(implemented) >= 4 and uses_time_provider
    return check("D06", "CODE.8", ok, f"{len(names)} interfaces, {len(implemented)} with an implementation"
                 f"{', time through TimeProvider or IClock' if uses_time_provider else ', no TimeProvider or IClock'}")


def web_contract(root):
    """OBS.1 and OBS.3 for an application: stable error codes and its own health endpoint."""
    names = [rel.name for rel, _ in files(root, {".cs"}) if "tests" not in rel.parts]
    bodies = "\n".join(text(p) for rel, p in files(root, {".cs"}) if "tests" not in rel.parts)
    catalogue = any(re.search(r"(Error|Reason|Failure)Codes?\b", n) for n in names)
    health = re.search(r"Map(Get|Methods)\s*\(\s*\"[^\"]*health", bodies, re.I) is not None or "MapHealthChecks" in bodies
    return check("D08", "OBS.1", catalogue and health,
                 f"error-code catalogue {'yes' if catalogue else 'no'}; health endpoint {'yes' if health else 'no'}")


def concrete_construction(root):
    interface_impls = set()
    sources = [(rel, text(p)) for rel, p in files(root, {".cs"}) if "tests" not in rel.parts]
    for _, body in sources:
        for m in re.finditer(r"class\s+(\w+)[^{;]*?:\s*[^{;]*\bI[A-Z]\w+", body):
            interface_impls.add(m.group(1))
    offenders = []
    for rel, body in sources:
        if not re.search(r"(Operation|Service|Handler|Manager)\.cs$", rel.name):
            continue
        for name in interface_impls:
            if re.search(r"\bnew\s+" + re.escape(name) + r"\s*[(\[{]", body) and not re.search(r"class\s+" + re.escape(name) + r"\b", body):
                offenders.append(f"{rel.as_posix()} builds {name}")
    return check("D07", "CODE.8", not offenders and bool(interface_impls),
                 f"{len(interface_impls)} implementations of interfaces; built inside Operation/Service/Handler classes: {offenders[:6] or 'none'}")


def observability_contract(root):
    names = [rel.name for rel, _ in files(root, {".cs"}) if "tests" not in rel.parts]
    bodies = "\n".join(text(p) for rel, p in files(root, {".cs"}) if "tests" not in rel.parts)
    catalogue = any(re.search(r"(Error|Reason|Failure)Codes?\b", n) for n in names)
    events = any(re.search(r"Event(s|Names|Catalog)", n) for n in names) or "RunStarted" in bodies or "run_started" in bodies
    status = re.search(r"\"(status|health)\"", bodies) is not None or re.search(r"class\s+\w*(Status|Health)\w*", bodies) is not None
    return check("D08", "OBS.3", catalogue and events and status,
                 f"error-code catalogue {'yes' if catalogue else 'no'}; event names {'yes' if events else 'no'}; "
                 f"status or health call {'yes' if status else 'no'}")


def test_layers(root):
    tests = [(rel, text(p)) for rel, p in files(root, {".cs"}) if "tests" in rel.parts]
    total = sum(len(re.findall(r"\[(Fact|Theory|Test|TestCase)\b", b)) for _, b in tests)
    through_main = sum(len(re.findall(r"Program\.Main|Process\.Start|RunProcess", b)) for _, b in tests)
    units = [rel.name for rel, b in tests if re.search(r"\[(Fact|Theory|Test)\b", b)
             and not re.search(r"Program\.Main|Process\.Start", b)]
    return check("D09", "T.3", total >= 12 and len(units) >= 3,
                 f"{total} tests; {len(units)} file(s) test a component without the entry point ({units[:5]}); "
                 f"{through_main} reference the entry point")


def run(root, profile="service", design_only=False):
    service = profile == "service"
    web = profile == "web-app"
    checks = [design_document(root), adrs(root, 2 if service or web else 1), repo_agents(root)]
    if design_only:  # the gate before src/: the design exists, the code is not judged yet
        failed = [c["id"] for c in checks if c["status"] == "fail"]
        return {"status": "pass" if not failed else "fail", "profile": profile, "failed": failed, "checks": checks,
                "note": "design files only; the code checks run in the project verify and CI"}
    checks += [verify_command(root), composition_root(root), concrete_construction(root), test_layers(root)]
    if service:
        checks += [interfaces(root), observability_contract(root)]
    if web:
        checks += [ports(root), web_contract(root)]
    checks.sort(key=lambda c: c["id"])
    failed = [c["id"] for c in checks if c["status"] == "fail"]
    return {"status": "pass" if not failed else "fail", "profile": profile, "failed": failed, "checks": checks,
            "note": "structural evidence only; a reviewer reads the design and the ADRs"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", nargs="?", default=".")
    parser.add_argument("--profile", choices=["generic", "service", "web-app"], default="generic")
    parser.add_argument("--design-only", action="store_true", help="check only the design, ADRs and AGENTS.md (before src/)")
    parser.add_argument("--json", action="store_true", help="print the full result instead of the failing checks")
    args = parser.parse_args()
    result = run(pathlib.Path(args.workspace).resolve(), args.profile, args.design_only)
    if args.json:
        json.dump(result, sys.stdout, indent=2)
        print()
    else:
        for c in result["checks"]:
            if c["status"] == "fail":
                print(f"design-check {c['id']} ({c['rule']}): {c['detail']}", file=sys.stderr)
        print(f"design-check ({args.profile}): {result['status']}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
