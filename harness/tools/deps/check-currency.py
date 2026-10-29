#!/usr/bin/env python3
"""Deterministic check for rule DEL.2: runtime and framework versions are the current stable release or the one before.

Input:  a repo (--repo, default the current directory) and what is current, from files only. This script never
        calls the network, so the gate gives the same answer in CI as on a laptop:
          --current FILE          JSON the team maintains: {"asof": "2026-10-28", "dotnet": 10, "node": 24,
                                  "packages": {"react": "19.1.0", "Microsoft.EntityFrameworkCore": "10.0.0"}}
          --dotnet-outdated FILE  output of `dep-read.sh dotnet list package --outdated` (text, or --format json)
          --npm-outdated FILE     output of `dep-read.sh npm outdated --json` (or `pnpm outdated --format json`)
        Optionally the PR description (--description) for the waiver, and the changed paths (--changed FILE, or -
        for stdin) to look only at manifests the PR touches. Without --changed the whole repo is read.
Output: `path:line: DEL.2 message` per hit; exit 0 pass, 1 findings, 2 usage or unusable input.

What it reads (DEL.2 applies_to): *.csproj TargetFramework(s), Directory.Build.props, Directory.Packages.props,
global.json sdk.version, package.json engines.node and dependencies.

DEL.2 counts releases: with current major N, N and N-1 pass and N-2 or older fail. For .NET a release is the
major (net10.0), for packages the major version. Which packages are "frameworks" is not stated by the rule: the
default list below is checked (override with "frameworks" in .harness-currency.json, or check every package
with --all-packages).

Waiver: a PR description line `deps: n/a - <reason of at least 10 characters>` that includes the backlog item
(a URL or an id such as AB#1234), because DEL.2 asks for an upgrade item on the backlog, linked in the PR.

Example:
  .harness/tools/deps/dep-read.sh dotnet list package --outdated --format json > outdated.json
  python3 .harness/tools/deps/check-currency.py --current currency.json --dotnet-outdated outdated.json \\
      --description pr.txt
"""

import argparse
import datetime
import fnmatch
import json
import os
import pathlib
import re
import sys

sys.dont_write_bytecode = True  # keep the bundle free of __pycache__ folders

WAIVER = re.compile(r"^\s*deps:\s*n/a\s*-\s*(.{10,})$", re.I | re.M)
BACKLOG_LINK = re.compile(r"https?://\S+|\b[A-Za-z][A-Za-z0-9]*#\d+")
SKIP_DIRS = {".git", "node_modules", "bin", "obj", "dist", "packages", ".vs", ".idea", ".harness"}
DEFAULT_FRAMEWORKS = [
    # .NET
    "Microsoft.AspNetCore.*", "Microsoft.EntityFrameworkCore*", "Microsoft.Extensions.*",
    # JavaScript
    "react", "react-dom", "next", "vue", "nuxt", "svelte", "@angular/core", "@angular/common",
]
CONFIG_NAME = ".harness-currency.json"


class Usage(Exception):
    """Unusable input: reported on stderr, exit 2."""


def major(text):
    m = re.match(r"^[\s^~<>=v\[(]*(\d+)", str(text))
    return int(m.group(1)) if m else None


def blank_comments(text):
    return re.sub(r"<!--.*?-->", lambda m: re.sub(r"[^\n]", " ", m.group()), text, flags=re.S)


def line_of(text, offset):
    return text.count("\n", 0, offset) + 1


def line_with(text, needle, start=0):
    i = text.find(needle, start)
    return line_of(text, i) if i >= 0 else 1


# ---------------------------------------------------------------- what is current

def load_current(path, today, max_age):
    notes = []
    if not path:
        return {"dotnet": None, "node": None, "packages": {}}, notes
    try:
        data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise Usage(f"--current {path}: {e}")
    if not isinstance(data, dict):
        raise Usage(f"--current {path}: expected a JSON object")
    current = {"dotnet": None, "node": None, "packages": {}}
    for key in ("dotnet", "node"):
        if data.get(key) is not None:
            current[key] = major(data[key])
            if current[key] is None:
                raise Usage(f"--current {path}: '{key}' is not a version: {data[key]!r}")
    for name, version in (data.get("packages") or {}).items():
        if major(version) is None:
            raise Usage(f"--current {path}: package '{name}' has no version: {version!r}")
        current["packages"][name.lower()] = str(version)
    asof = data.get("asof")
    if not asof:
        notes.append(f"note: {path} has no 'asof' date, so its age cannot be judged")
    else:
        try:
            age = (today - datetime.date.fromisoformat(asof)).days
        except ValueError:
            raise Usage(f"--current {path}: 'asof' is not a YYYY-MM-DD date: {asof!r}")
        if max_age is not None and age > max_age:
            raise Usage(f"--current {path} is {age} days old (asof {asof}), over --max-age-days {max_age}; refresh it")
        if age > 120:
            notes.append(f"note: current-version data is {age} days old (asof {asof}); a newer release may exist")
    return current, notes


def read_text(path, flag):
    try:
        return pathlib.Path(path).read_text(encoding="utf-8")
    except OSError as e:
        raise Usage(f"{flag} {path}: {e}")


def parse_dotnet_outdated(path):
    """-> {name.lower(): (name, resolved, latest)} from `dotnet list package --outdated`, text or json."""
    text = read_text(path, "--dotnet-outdated")
    found = {}
    if text.lstrip().startswith("{"):
        try:
            data = json.loads(text)
        except ValueError as e:
            raise Usage(f"--dotnet-outdated {path}: {e}")
        for problem in data.get("problems", []):
            raise Usage(f"--dotnet-outdated {path}: dotnet reported: {problem.get('text', problem)}")
        for project in data.get("projects", []):
            for framework in project.get("frameworks", []):
                for group in ("topLevelPackages", "transitivePackages"):
                    for pkg in framework.get(group, []):
                        if pkg.get("id") and pkg.get("resolvedVersion") and pkg.get("latestVersion"):
                            found[pkg["id"].lower()] = (pkg["id"], pkg["resolvedVersion"], pkg["latestVersion"])
        return found
    if re.search(r"No assets file was found|run restore", text, re.I):
        raise Usage(f"--dotnet-outdated {path}: the project was not restored; a human runs dotnet restore first")
    header = None  # columns of the table we are in; only `Latest` tables are outdated tables
    for line in text.splitlines():
        if re.search(r"\bPackage\b", line) and "Latest" in line and "Resolved" in line:
            header = "requested" if "Requested" in line else "transitive"
            continue
        if re.search(r"\bPackage\b", line) and "Latest" not in line:
            header = None
            continue
        m = re.match(r"^\s*>\s+(\S+)\s+(.*\S)\s*$", line)
        if m and header:
            cells = m.group(2).split()
            if len(cells) >= 2:
                found[m.group(1).lower()] = (m.group(1), cells[-2], cells[-1])
    return found


def parse_npm_outdated(path):
    """-> {name.lower(): (name, current, latest)} from `npm outdated --json` or `pnpm outdated --format json`."""
    text = read_text(path, "--npm-outdated")
    if not text.strip():
        return {}  # npm prints nothing when everything is current
    try:
        data = json.loads(text)
    except ValueError:
        raise Usage(f"--npm-outdated {path}: not JSON; run npm outdated --json (pnpm outdated --format json)")
    if not isinstance(data, dict):
        raise Usage(f"--npm-outdated {path}: expected a JSON object keyed by package")
    found = {}
    for name, entry in data.items():
        for e in entry if isinstance(entry, list) else [entry]:
            if isinstance(e, dict) and e.get("current") and e.get("latest"):
                found[name.lower()] = (name, e["current"], e["latest"])
    return found


# ---------------------------------------------------------------- what the repo declares

def classify_tfm(tfm):
    t = tfm.strip().lower()
    if "$(" in t:
        return "unresolved", None
    t = t.split("-")[0]  # net8.0-windows10.0.19041
    m = re.fullmatch(r"net(\d+)\.(\d+)", t)
    if m and int(m.group(1)) >= 5:
        return "dotnet", int(m.group(1))
    m = re.fullmatch(r"netcoreapp(\d+)\.(\d+)", t)
    if m:
        return "dotnet", int(m.group(1))
    if re.fullmatch(r"net\d{2,3}", t):
        return "netfx", None
    if t.startswith("netstandard"):
        return "netstandard", None
    return "unknown", None


def scan_msbuild(rel, text):
    """Yield ('tfm', value, line) and ('pkg', name, version, line) from a project or props file."""
    text = blank_comments(text)
    for m in re.finditer(r"<(TargetFrameworks?|TargetFrameworkVersion)\b[^>]*>(.*?)</\1\s*>", text, re.S | re.I):
        tag, value = m.group(1), m.group(2).strip()
        line = line_of(text, m.start())
        if tag.lower() == "targetframeworkversion":
            yield ("tfm", "net" + re.sub(r"[^\d]", "", value.lstrip("vV")), line)
            continue
        for tfm in (v for v in value.split(";") if v.strip()):
            yield ("tfm", tfm.strip(), line)
    for m in re.finditer(r"<(PackageReference|PackageVersion)\b([^>]*?)(/?)>", text, re.S | re.I):
        attrs = m.group(2)
        name = re.search(r"\b(?:Include|Update)\s*=\s*\"([^\"]+)\"", attrs, re.I)
        version = re.search(r"\b(?:Version|VersionOverride)\s*=\s*\"([^\"]+)\"", attrs, re.I)
        if not name:
            continue
        if not version and not m.group(3):
            body = text[m.end():text.find("</" + m.group(1), m.end())]
            child = re.search(r"<Version>\s*([^<]+?)\s*</Version>", body, re.I)
            version = child
        yield ("pkg", name.group(1), version.group(1) if version else None, line_of(text, m.start()))


def scan_global_json(text):
    try:
        data = json.loads(text)
    except ValueError:
        return None, 1
    version = (data.get("sdk") or {}).get("version") if isinstance(data, dict) else None
    return version, line_with(text, '"version"')


def scan_package_json(text):
    try:
        data = json.loads(text)
    except ValueError:
        return None, [], 1
    if not isinstance(data, dict):
        return None, [], 1
    node = (data.get("engines") or {}).get("node")
    pkgs = []
    for section in ("dependencies", "devDependencies", "optionalDependencies"):
        start = text.find(f'"{section}"')
        for name, spec in (data.get(section) or {}).items():
            pkgs.append((name, str(spec), line_with(text, f'"{name}"', max(start, 0))))
    return node, pkgs, line_with(text, '"node"')


def find_manifests(repo, changed):
    names = {"directory.build.props", "directory.packages.props", "global.json", "package.json"}
    suffixes = (".csproj", ".fsproj", ".vbproj")
    if changed is not None:
        candidates = [pathlib.Path(p) for p in changed]
        for p in sorted(candidates):
            if (p.name.lower() in names or p.suffix.lower() in suffixes) and (repo / p).is_file():
                yield p
        return
    for root, dirs, files in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            if f.lower() in names or f.lower().endswith(suffixes):
                yield (pathlib.Path(root) / f).relative_to(repo)


# ---------------------------------------------------------------- the check

def run(args):
    repo = pathlib.Path(args.repo)
    if not repo.is_dir():
        raise Usage(f"--repo {args.repo}: not a directory")
    today = datetime.date.fromisoformat(args.today) if args.today else datetime.date.today()
    current, notes = load_current(args.current, today, args.max_age_days)
    outdated = {"nuget": {}, "npm": {}}
    for path in args.dotnet_outdated:
        outdated["nuget"].update(parse_dotnet_outdated(path))
    for path in args.npm_outdated:
        outdated["npm"].update(parse_npm_outdated(path))

    has_outdated_input = {"nuget": bool(args.dotnet_outdated), "npm": bool(args.npm_outdated)}
    frameworks = DEFAULT_FRAMEWORKS
    config = repo / CONFIG_NAME
    if config.is_file():
        try:
            frameworks = list(json.loads(config.read_text(encoding="utf-8"))["frameworks"])
        except (ValueError, KeyError, TypeError) as e:
            raise Usage(f"{config}: expected {{\"frameworks\": [\"glob\", ...]}} ({e})")

    def is_framework(name):
        return args.all_packages or any(fnmatch.fnmatch(name.lower(), g.lower()) for g in frameworks)

    changed = None
    if args.changed:
        raw = sys.stdin.read() if args.changed == "-" else read_text(args.changed, "--changed")
        changed = [os.path.normpath(line.strip()) for line in raw.splitlines() if line.strip()]

    hits, tfms, sdks, pkgs, needs = [], 0, 0, 0, set()
    declared = {}  # (ecosystem, name.lower()) -> (name, version, where)

    def need(key):
        needs.add(key)
        return current[key]

    for rel in find_manifests(repo, changed):
        name = rel.name.lower()
        text = (repo / rel).read_text(encoding="utf-8", errors="replace")
        where = rel.as_posix()
        if name == "global.json":
            version, line = scan_global_json(text)
            if version is None:
                continue
            have = major(version)
            sdks += 1
            cur = need("dotnet")
            if cur is not None and have is not None and cur - have >= 2:
                hits.append((where, line, f"SDK {version} is {cur - have} release(s) behind current .NET {cur}; "
                                          f"allowed SDK majors: {cur}, {cur - 1}"))
        elif name == "package.json":
            node, deps, node_line = scan_package_json(text)
            if node:
                majors = [int(n) for n in re.findall(r"(?<![\d.])(\d+)(?:\.[\dx*]+)*", node)]
                have = min(majors) if majors else None
                sdks += 1
                cur = need("node")
                if cur is not None and have is not None and cur - have >= 2:
                    hits.append((where, node_line, f"engines.node \"{node}\" allows Node {have}, {cur - have} release(s) behind "
                                                   f"current Node {cur}; allowed: {cur}, {cur - 1}"))
            for pname, spec, line in deps:
                declared[("npm", pname.lower())] = (pname, spec, f"{where}:{line}")
        else:
            for item in scan_msbuild(where, text):
                if item[0] == "tfm":
                    kind, have = classify_tfm(item[1])
                    tfms += 1
                    if kind == "dotnet":
                        cur = need("dotnet")
                        if cur is not None and cur - have >= 2:
                            hits.append((where, item[2], f"target framework {item[1].strip()} is {cur - have} release(s) behind "
                                                         f"current net{cur}.0; allowed: net{cur}.0, net{cur - 1}.0"))
                    elif kind == "netfx":
                        cur = need("dotnet")
                        if cur is not None:
                            hits.append((where, item[2], f"target framework {item[1].strip()} (.NET Framework) is older than "
                                                         f"the allowed net{cur}.0, net{cur - 1}.0"))
                    elif kind == "netstandard":
                        notes.append(f"note: {where}:{item[2]}: {item[1].strip()} is a compatibility contract, not a runtime; not judged")
                    else:
                        notes.append(f"note: {where}:{item[2]}: target framework '{item[1].strip()}' not resolved; not judged")
                else:
                    _, pname, version, line = item
                    declared.setdefault(("nuget", pname.lower()), (pname, version, f"{where}:{line}"))

    for eco in ("nuget", "npm"):  # what the package manager resolved beats the declared range
        for key, (pname, resolved, _latest) in outdated[eco].items():
            location = declared.get((eco, key), (None, None, f"<{eco} outdated input>"))[2]
            declared[(eco, key)] = (pname, resolved, location)

    for (eco, key), (pname, version, location) in sorted(declared.items(), key=lambda kv: kv[1][2]):
        if not is_framework(pname):
            continue
        path, _, line = location.rpartition(":")
        line = int(line) if line.isdigit() else 1
        have = major(version) if version else None
        if have is None:
            if version and "$(" in version:
                notes.append(f"note: {location}: {pname} version '{version}' is not resolved; not judged")
            continue
        latest = outdated[eco].get(key, (None, None, None))[2] or current["packages"].get(key)
        if latest is None:
            if has_outdated_input[eco]:
                latest = version  # absent from an outdated listing means up to date
            else:
                notes.append(f"note: {location}: no current version of {pname} supplied; not judged")
                continue
        cur = major(latest)
        pkgs += 1
        if cur is not None and cur - have >= 2:
            shown = re.sub(r"^[\s^~<>=v\[(]+", "", version)
            hits.append((path, line, f"package {pname} {shown} is {cur - have} major(s) behind current {latest}; "
                                     f"allowed majors: {cur}, {cur - 1}"))

    missing = [k for k in needs if current[k] is None]
    if missing:
        raise Usage("the repo declares " + " and ".join(
            {"dotnet": ".NET target frameworks or an SDK pin", "node": "engines.node"}[k] for k in sorted(missing)) +
            "; --current must give " + " and ".join(f"'{k}'" for k in sorted(missing)) + ", or the gate would pass blind")
    return sorted(set(hits)), notes, (tfms, sdks, pkgs)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="repository root (default: the current directory)")
    parser.add_argument("--current", help="JSON file with the current stable runtime and package versions")
    parser.add_argument("--dotnet-outdated", action="append", default=[], metavar="FILE",
                        help="output of dep-read.sh dotnet list package --outdated (text or --format json)")
    parser.add_argument("--npm-outdated", action="append", default=[], metavar="FILE",
                        help="output of dep-read.sh npm outdated --json")
    parser.add_argument("--description", help="file with the PR description, for the waiver line")
    parser.add_argument("--changed", metavar="FILE", help="changed paths, one per line ('-' for stdin); default: the whole repo")
    parser.add_argument("--all-packages", action="store_true", help="judge every package, not only the framework list")
    parser.add_argument("--max-age-days", type=int, help="exit 2 when the --current data is older than this")
    parser.add_argument("--today", help="YYYY-MM-DD, for tests")
    args = parser.parse_args()
    try:
        hits, notes, (tfms, sdks, pkgs) = run(args)
        description = pathlib.Path(args.description).read_text(encoding="utf-8") if args.description else ""
    except (Usage, OSError, ValueError) as e:
        print(f"check-currency: {e}", file=sys.stderr)
        return 2
    for note in notes:
        print(note)
    for path, line, message in hits:
        print(f"{path}:{line}: DEL.2 {message}")
    checked = f"checked {tfms} target framework(s), {sdks} runtime/SDK pin(s), {pkgs} package(s)"
    waiver = WAIVER.search(description)
    if hits and waiver and BACKLOG_LINK.search(waiver.group(1)):
        print(f"deps check: {len(hits)} hit(s) waived by the PR description: {waiver.group(1).strip()} ({checked})")
        return 0
    if hits and waiver:
        print("DEL.2: the waiver needs the backlog item; add its URL or id (for example AB#1234) to the `deps: n/a` line.")
    elif hits:
        print("DEL.2: move to the current release or the one before, or add `deps: n/a - <reason and backlog item link>` "
              "to the PR description.")
    print(f"deps check: {len(hits)} hit(s) ({checked})")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
