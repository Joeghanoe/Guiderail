#!/usr/bin/env python3
"""Coverage and impact of a change: which tests execute the changed code, and what is left uncovered.

Informational, not a gate. It exits 0 whenever it can produce an answer, whatever the coverage is. There is no
threshold on purpose: a coverage threshold is a policy the harness has not set, and a number invented here would
be a rule nobody reviewed. It reports the number and the reviewer judges. Rule T.5 stays with
tools/testing/check-scenarios.py (a scenario file was touched); this tool does not repeat that check. It gives
the evidence behind T.1 ("done means verified"), the layer view of T.3 and the signal for T.4 (what a later layer
would find first).

What the numbers do NOT show (the output repeats this):
  * Line coverage shows a line was executed, not that behaviour was asserted. A line run only incidentally by an
    unrelated test is reported as covered here and is not verified. A green number is not proof.
  * Cobertura (coverlet) and lcov without TN: records do not say which test case ran a line. The unit is then the
    report, i.e. the test suite it came from. Test-case names appear only for lcov reports with TN: records.
  * The layer (unit / integration / e2e) is inferred from the report label or path, or from the TN: name. It is
    a convention, not a fact: label the reports yourself (--report integration=path) when the path says nothing.
  * "Not in any report" means no supplied report mentions the file: no test loaded it, or it is excluded from
    instrumentation (generated code, ExcludeByFile), or the report is the wrong one.
  * Changed lines come from --diff. Without it the numbers describe the whole file, not your change.
  * Instrumented lines only: comments, blank lines, braces and declarations are not in a report and are not
    counted as covered or uncovered.

Input:
  stdin     changed paths, one per line (as check-scenarios.py), relative to --root. `git diff --name-status -M`
            lines (`M<TAB>path`, `R100<TAB>old<TAB>new`, `D<TAB>path`) are accepted too.
  --diff    a unified diff (`git diff -U0 -M origin/main...HEAD`) for changed-line precision and renames. Its
            files are added to the stdin set. Expects git's default a/ b/ prefixes.
  --report  [LABEL=]PATH, repeatable: a Cobertura XML (dotnet test --collect:"XPlat Code Coverage") or an lcov
            file. The format is detected by content, not by extension. Give one report per test suite or layer to
            get the layer view: --report unit=a.xml --report integration=b.xml --report e2e=c.info
  --root    the repository root (default: the current directory). Changed paths and report paths are confined
            to it; a path with `..` or outside the root is rejected, never opened.
  --json    machine output (schema below) instead of the summary.
  The tool never runs tests or git; running verify is the agent's decision (scripts/verify.sh).

Exit codes: 0 an answer was produced (including "nothing changed" and every warning below);
            2 usage error, report missing or unparseable (no answer).

Warnings appear in the summary and in the JSON `warnings`: a report older than a changed file
(`stale`), a changed file absent from the report, a renamed file the report only knows by its old name, a changed
path outside the root, a report with no layer signal, a single layer supplied, ignored report paths.

--json schema (schema_version 1; keys are always present; new keys may be added, none renamed or removed
without bumping schema_version):
  {
    "schema_version": 1, "tool": "coverage-impact", "informational": true,
    "limits": [string], "warnings": [string], "root": string,
    "reports": [{"label", "path", "format": "cobertura"|"lcov", "layer": "unit"|"integration"|"e2e"|"unknown",
                 "layer_basis": "label"|"path"|"default"|"none", "generated_at": ISO-8601 UTC|null,
                 "generated_at_source": "report"|"mtime"|null, "files": int, "ignored_paths": int,
                 "per_test_names": bool}],
    "layers_supplied": [layer],
    "stale": {"checked": bool, "is_stale": bool,
              "files": [{"path", "modified_at", "report"}], "renamed_unknown_to_report": [path]},
    "summary": {"granularity": "lines"|"file"|"mixed"|"none",
                "changed_files": int, "by_status": {status: int},
                "executable_lines": int, "covered_lines": int, "uncovered_lines": int,
                "line_coverage": float 0..1|null,
                "uncovered_files": [path],              # not_in_report, uncovered, partial, ambiguous
                "covered_lines_by_layer": {layer: int},  # lines executed by that layer (a line may count in several)
                "covered_only_by_layer": {layer: int},   # lines executed by that layer and no other
                "files_covered_only_by": {layer: [path]}},
    "files": [{"path", "old_path": string|null,
               "status": "covered"|"partial"|"uncovered"|"not_in_report"|"ambiguous"|"no_executable_lines"|
                         "deleted"|"test_file"|"not_code"|"rejected",
               "granularity": "lines"|"file"|"none",
               "executable_lines": int, "covered_lines": int, "uncovered_lines": int, "line_coverage": float|null,
               "uncovered_ranges": [[first, last]],
               "report_match": [{"report", "path", "match": "exact"|"suffix"}],
               "covered_by": [{"report", "layer", "layers": [layer], "lines": int,
                               "tests": [string]|null, "tests_total": int|null}],
               "covering_layers": [layer], "exclusive_lines": {layer: int}, "notes": [string]}]
  }
  Paths in the JSON are repo-relative with forward slashes. `rejected` entries keep the offending text, escaped.

Tool contract (Vegviser AI Tool Boundary)
  Classification:  Read. No state change, no network, no secrets.
  Owner:           team:teamvalue-aicoe. Version: the harness commit in .harness/VERSION.
  Caller identity: none. Runs as the caller, uses no credentials, never logs in.
  Inputs:          changed paths (stdin), an optional unified diff, and one or more coverage reports (Cobertura
                   XML, lcov). All of it is untrusted data (SEC.1): a path or test name inside a report or diff is
                   matched as a string and never opened or executed; XML with entity declarations is refused.
  Results:         a summary or JSON on stdout; exit 0 with an answer, exit 2 on usage or an unparseable report.
                   It never fails on low coverage.
  Side effects:    none. Reads the named report and diff, and stats changed paths that resolve inside --root (for
                   the staleness check). Writes nothing. Does not run tests or git.
  Review trigger:  a new report format, any change to the --json schema (bump schema_version), or a proposal to
                   turn it into a gate (that needs a threshold policy first, set by a human).

Examples:
  git diff --name-only origin/main...HEAD | python3 .harness/tools/testing/coverage-impact.py \\
    --report unit=tests/Unit/TestResults/coverage.cobertura.xml --report e2e=coverage/lcov.info
  python3 .harness/tools/testing/coverage-impact.py --diff pr.diff --report coverage.cobertura.xml --json </dev/null
"""

import argparse
import datetime
import json
import os
import posixpath
import re
import sys

import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True  # keep the bundle free of __pycache__ folders

SCHEMA_VERSION = 1
LAYERS = ("unit", "integration", "e2e", "unknown")
MAX_BYTES = 256 * 1024 * 1024
TOLERANCE_SECONDS = 2
SHOWN_TESTS = 20

LIMITS = [
    "Line coverage shows a line was executed, not that behaviour was asserted. A line covered only incidentally "
    "by an unrelated test is reported as covered and is not verified; a green number is not proof.",
    "Cobertura and lcov without TN: records do not say which test case ran a line: the unit is the report "
    "(test suite). Test-case names appear only for lcov with TN: records.",
    "The layer is inferred from the report label, path or test name; it is a convention. Label reports with "
    "--report <layer>=<path> when the path says nothing.",
    "Only instrumented lines count. Comments, blank lines, braces and declarations are neither covered nor uncovered.",
]
NO_THRESHOLD = (
    "No threshold on purpose: a coverage threshold is a policy the harness has not set, and inventing one here "
    "would be an unreviewed rule. The tool reports the number, exits 0, and the reviewer judges."
)

CODE_SUFFIXES = {".cs", ".vb", ".fs", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".razor", ".cshtml", ".py"}
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")
E2E_WORDS = re.compile(r"e2e|end[-_. ]?to[-_. ]?end|acceptance|playwright|cypress|selenium|smoke|journey", re.I)
INTEGRATION_WORDS = re.compile(r"integration|contract|functional", re.I)
UNIT_WORDS = re.compile(r"unit", re.I)
GENERIC_TEST = re.compile(r"(?:^|[/._-])(?:tests?|specs?|__tests__)(?:$|[/._-])|[a-z0-9]Tests?(?:$|[/._-])")
TEST_DIR = re.compile(r"(?:^|[._-])(?:tests?|specs?)$|[a-z0-9]Tests?$|^__tests__$|^(?:e2e|cypress|playwright)$", re.I)
TEST_FILE_LOWER = re.compile(r"[._-](?:tests?|specs?)\.[a-z0-9]+$")
TEST_FILE_CAMEL = re.compile(r"[a-z0-9]Tests?\.[A-Za-z0-9]+$")
HUNK = re.compile(r"^@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
OLD_COUNT = re.compile(r"^@@ -\d+(?:,(\d+))? ")


class ReportError(Exception):
    """A report or diff that cannot be read: exit 2."""


def clean(value, limit=200):
    """Printable text for an untrusted string: control characters (ANSI escapes included) become `?`."""
    text = CONTROL.sub("?", str(value))
    return text if len(text) <= limit else text[: limit - 3] + "..."


def iso(epoch):
    if epoch is None:
        return None
    return datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ranges(numbers):
    out = []
    for n in sorted(numbers):
        if out and n == out[-1][1] + 1:
            out[-1][1] = n
        else:
            out.append([n, n])
    return out


def fmt_ranges(spans, limit=12):
    parts = [str(a) if a == b else f"{a}-{b}" for a, b in spans]
    return ", ".join(parts[:limit]) + (f", ... (+{len(parts) - limit} more)" if len(parts) > limit else "")


# ---------------------------------------------------------------------------------------------- paths

def root_variants(root):
    """The root as given and with symlinks resolved (macOS /var vs /private/var), as plain strings."""
    variants = []
    for candidate in (os.path.abspath(root), os.path.realpath(root)):
        candidate = candidate.replace("\\", "/").rstrip("/") or "/"
        if candidate not in variants:
            variants.append(candidate)
    return variants


def relative_to_root(path, roots):
    for root in roots:
        if path == root:
            return ""
        if path.startswith(root.rstrip("/") + "/"):
            return path[len(root.rstrip("/")) + 1:]
    return None


def split_drive(path):
    match = re.match(r"^[A-Za-z]:(?=/)", path)
    return (True, path[match.end():]) if match else (False, path)


def normalize_path(raw, roots):
    """Return (path, reason). path is repo-relative when the input is under the root, or an absolute foreign path
    (report paths from another machine); None with a reason when it must not be used. A `..` component, a
    control character or an empty path is refused before any normalisation. Nothing here touches the filesystem."""
    if raw is None or not str(raw).strip():
        return None, "empty path"
    text = str(raw).strip()
    if CONTROL.search(text):
        return None, "control character in path"
    text = text.replace("\\", "/")
    drive, text = split_drive(text)
    text = re.sub(r"/{2,}", "/", text)
    if ".." in text.split("/"):
        return None, "'..' component"
    absolute = text.startswith("/") or drive
    text = posixpath.normpath(text)
    if text == ".":
        return None, "empty path"
    if absolute:
        rel = relative_to_root(text, roots)
        if rel:
            return rel, None
        return text if text.startswith("/") else "/" + text, None
    return text.lstrip("/"), None


def safe_stat(root, rel):
    """mtime of root/rel, only when it resolves (symlinks included) inside the root; else None."""
    real_root = os.path.realpath(root)
    full = os.path.realpath(os.path.join(real_root, rel))
    if full != real_root and not full.startswith(real_root + os.sep):
        return None
    try:
        return os.stat(full).st_mtime
    except OSError:
        return None


def git_unquote(text):
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        body, out, i = text[1:-1], bytearray(), 0
        simple = {"n": 10, "t": 9, '"': 34, "\\": 92}
        while i < len(body):
            ch = body[i]
            if ch == "\\" and i + 1 < len(body):
                nxt = body[i + 1]
                if nxt in simple:
                    out.append(simple[nxt])
                    i += 2
                    continue
                octal = re.match(r"[0-7]{1,3}", body[i + 1:])
                if octal:
                    out.append(int(octal.group(0), 8) & 0xFF)
                    i += 1 + len(octal.group(0))
                    continue
            out.extend(ch.encode("utf-8"))
            i += 1
        return out.decode("utf-8", errors="replace")
    return text


# -------------------------------------------------------------------------------------- layer inference

def infer_layer(text):
    """(layer, basis) from a label, path or test name. basis: matched | default | none."""
    if E2E_WORDS.search(text):
        return "e2e", "matched"
    if INTEGRATION_WORDS.search(text):
        return "integration", "matched"
    if UNIT_WORDS.search(text):
        return "unit", "matched"
    if GENERIC_TEST.search(text):
        return "unit", "default"
    return "unknown", "none"


def is_test_path(path):
    parts = path.split("/")
    if any(TEST_DIR.search(part) for part in parts[:-1]):
        return True
    name = parts[-1]
    return bool(TEST_FILE_LOWER.search(name.lower()) or TEST_FILE_CAMEL.search(name))


# ------------------------------------------------------------------------------------- report parsing

class Report:
    def __init__(self, label, path, fmt):
        self.label, self.path, self.format = label, path, fmt
        self.layer, self.layer_basis = "unknown", "none"
        self.generated_at = self.generated_source = None
        self.lines = {}      # path -> {line: hits}
        self.tests = {}      # path -> {line: {test name}}; "" is a hit by an unnamed test (lcov)
        self.ignored = 0
        self.by_basename = {}
        self.per_test_names = False

    def add_line(self, path, number, hits, test=None):
        entry = self.lines.setdefault(path, {})
        entry[number] = max(entry.get(number, 0), hits)
        if test is not None and hits > 0:
            self.tests.setdefault(path, {}).setdefault(number, set()).add(test)
            if test:
                self.per_test_names = True

    def index(self):
        for path in self.lines:
            self.by_basename.setdefault(path.rsplit("/", 1)[-1], []).append(path)

    def find(self, rel):
        """(path, kind) with kind exact|suffix|ambiguous|None. The report path may be absolute on another
        machine (suffix) or shorter than ours (relative to a project folder)."""
        if rel in self.lines:
            return rel, "exact"
        candidates = []
        for path in self.by_basename.get(rel.rsplit("/", 1)[-1], []):
            if path.startswith("/"):
                hit = path.endswith("/" + rel)
            else:
                hit = rel.endswith("/" + path)
            if hit:
                candidates.append(path)
        if len(candidates) == 1:
            return candidates[0], "suffix"
        return (None, "ambiguous") if candidates else (None, None)

    def layers_at(self, path, number):
        """Layers whose tests executed this line in this report."""
        if self.lines.get(path, {}).get(number, 0) <= 0:
            return set()
        names = self.tests.get(path, {}).get(number)
        if not names:
            return {self.layer}
        found = set()
        for name in names:
            layer, basis = infer_layer(name) if name else (self.layer, "none")
            found.add(layer if basis == "matched" else self.layer)
        return found

    def tests_at(self, path, numbers):
        names = set()
        for number in numbers:
            names |= self.tests.get(path, {}).get(number, set())
        return {n for n in names if n}


def sniff(text):
    head = text.lstrip("﻿ \t\r\n")
    if head.startswith("<"):
        return "cobertura"
    if re.search(r"^(?:TN|SF):", text[:200000], re.M):
        return "lcov"
    return None


def parse_epoch(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number > 1e11:  # Cobertura written in milliseconds
        number /= 1000
    if 946684800 <= number <= datetime.datetime.now().timestamp() + 86400:
        return number
    return None


def parse_cobertura(report, data, text, roots, root):
    if re.search(r"<!ENTITY", text, re.I):
        raise ReportError("XML entity declaration found; refusing to parse untrusted XML that defines entities")
    try:
        tree = ET.fromstring(data)
    except ET.ParseError as error:
        raise ReportError(f"not well-formed XML: {clean(error)}")
    if tree.tag != "coverage":
        raise ReportError(f"XML root is <{clean(tree.tag, 40)}>, not <coverage>: only Cobertura XML is supported")
    stamp = parse_epoch(tree.get("timestamp"))
    if stamp is not None:
        report.generated_at, report.generated_source = stamp, "report"
    sources = [(s.text or "").strip() for s in tree.iter("source") if (s.text or "").strip()]
    bad = 0
    for cls in tree.iter("class"):
        filename = cls.get("filename")
        if not filename:
            continue
        text_name = filename.replace("\\", "/")
        _, no_drive = split_drive(text_name)
        if no_drive.startswith("/") or text_name != no_drive or not sources:
            candidates = [filename]
        else:
            candidates = [source.rstrip("/\\") + "/" + filename for source in sources]
        resolved = None
        for candidate in candidates:  # first candidate that exists in the repo wins, else the first usable
            path, _ = normalize_path(candidate, roots)
            if path is None:
                continue
            if resolved is None:
                resolved = path
            if not path.startswith("/") and safe_stat(root, path) is not None:
                resolved = path
                break
        if resolved is None:
            report.ignored += 1
            continue
        report.lines.setdefault(resolved, {})
        for element in cls.iter("line"):
            try:
                number, hits = int(element.get("number")), int(float(element.get("hits", "0")))
            except (TypeError, ValueError):
                bad += 1
                continue
            if number < 1 or hits < 0:
                bad += 1
                continue
            report.add_line(resolved, number, hits)
    if bad:
        report.ignored += bad


def parse_lcov(report, text, roots):
    path, test = None, ""
    skipping = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("TN:"):
            test = line[3:].strip()
        elif line.startswith("SF:"):
            resolved, _ = normalize_path(line[3:], roots)
            if resolved is None:
                path, skipping = None, True
                report.ignored += 1
            else:
                path, skipping = resolved, False
                report.lines.setdefault(path, {})
        elif line.startswith("DA:") and path is not None:
            parts = line[3:].split(",")
            try:
                number, hits = int(parts[0]), int(float(parts[1]))
            except (ValueError, IndexError):
                report.ignored += 1
                continue
            if number < 1 or hits < 0:
                report.ignored += 1
                continue
            report.add_line(path, number, hits, test=test)
        elif line == "end_of_record":
            path, test, skipping = None, "", False


def load_report(spec, root, roots):
    label, location = None, spec
    if not os.path.exists(spec) and "=" in spec:
        head, tail = spec.split("=", 1)
        if re.fullmatch(r"[A-Za-z0-9_.@+-]{1,60}", head) and tail:
            label, location = head, tail
    if not os.path.isfile(location):
        raise ReportError(f"report not found: {clean(location)}")
    size = os.path.getsize(location)
    if size > MAX_BYTES:
        raise ReportError(f"report is larger than {MAX_BYTES // (1024 * 1024)} MB: {clean(location)}")
    with open(location, "rb") as handle:
        data = handle.read()
    text = data.decode("utf-8-sig", errors="replace")
    fmt = sniff(text)
    if fmt is None:
        raise ReportError(f"unrecognised coverage format (expected Cobertura XML or lcov): {clean(location)}")
    report = Report(label or os.path.basename(location), location, fmt)
    try:
        if fmt == "cobertura":
            parse_cobertura(report, data, text, roots, root)
        else:
            parse_lcov(report, text, roots)
    except ReportError as error:
        raise ReportError(f"{clean(location)}: {error}")
    if report.generated_at is None:
        try:
            report.generated_at, report.generated_source = os.stat(location).st_mtime, "mtime"
        except OSError:
            pass
    if label:
        report.layer, basis = infer_layer(label)
        report.layer_basis = "label" if basis == "matched" else "default" if basis == "default" else "none"
        if basis == "none":
            report.layer, basis = infer_layer(location)
            report.layer_basis = "path" if basis == "matched" else "default" if basis == "default" else "none"
    else:
        shown = relative_to_root(os.path.abspath(location).replace("\\", "/"), roots)
        report.layer, basis = infer_layer(shown if shown is not None else "/".join(location.replace("\\", "/").split("/")[-4:]))
        report.layer_basis = "path" if basis == "matched" else "default" if basis == "default" else "none"
    report.index()
    return report


# ------------------------------------------------------------------------------------ changed set

def parse_diff(text):
    entries, current = [], None
    old_left = new_left = new_line = 0
    for line in text.splitlines():
        if old_left > 0 or new_left > 0:  # inside a hunk: every line is content, even one that starts with ---
            if line.startswith("+"):
                current["lines"].add(new_line)
                new_line, new_left = new_line + 1, new_left - 1
            elif line.startswith("-"):
                old_left -= 1
            elif not line.startswith("\\"):
                new_line, old_left, new_left = new_line + 1, old_left - 1, new_left - 1
            continue
        if line.startswith("diff --git "):
            current = {"old": None, "new": None, "lines": set(), "deleted": False, "hunks": 0, "plus_seen": False}
            entries.append(current)
            rest = line[len("diff --git "):]
            if rest.startswith("a/") or rest.startswith('"a/'):
                bare = rest.replace('"a/', "a/", 1) if rest.startswith('"') else rest
                positions = [m.start() for m in re.finditer(r' "?b/', bare)]
                for pos in positions:
                    left, right = bare[2:pos], bare[pos:].strip().lstrip('"').removeprefix("b/").rstrip('"')
                    if left == right or pos == positions[-1]:
                        current["old"], current["new"] = git_unquote(left), git_unquote(right)
                        break
            continue
        if line.startswith("--- "):
            if current is None or current["plus_seen"]:
                current = {"old": None, "new": None, "lines": set(), "deleted": False, "hunks": 0, "plus_seen": False}
                entries.append(current)
            name = git_unquote(line[4:].split("\t")[0])
            current["old"] = None if name == "/dev/null" else (name[2:] if name.startswith("a/") else name)
        elif line.startswith("+++ ") and current is not None:
            name = git_unquote(line[4:].split("\t")[0])
            current["plus_seen"] = True
            if name == "/dev/null":
                current["deleted"], current["new"] = True, current["old"]
            else:
                current["new"] = name[2:] if name.startswith("b/") else name
        elif line.startswith("rename from ") and current is not None:
            current["old"] = git_unquote(line[len("rename from "):])
        elif line.startswith("rename to ") and current is not None:
            current["new"] = git_unquote(line[len("rename to "):])
        elif line.startswith("deleted file mode") and current is not None:
            current["deleted"] = True
        elif line.startswith("@@") and current is not None:
            match = HUNK.match(line)
            if match:
                old_count = OLD_COUNT.match(line).group(1)
                old_left = 1 if old_count is None else int(old_count)
                new_left = 1 if match.group(3) is None else int(match.group(3))
                new_line = int(match.group(2))
                current["hunks"] += 1
    return [e for e in entries if e["new"] or e["old"]]


def parse_stdin(text):
    out = []
    for raw in text.splitlines():
        line = raw.rstrip("\r\n")
        if not line.strip():
            continue
        if "\t" in line:
            parts = line.split("\t")
            status = parts[0].strip()[:1].upper()
            if status in ("R", "C") and len(parts) >= 3:
                out.append({"old": git_unquote(parts[1]), "new": git_unquote(parts[2]), "deleted": False, "lines": None})
                continue
            if len(parts) >= 2 and status in ("A", "M", "D", "T", "U"):
                out.append({"old": None, "new": git_unquote(parts[1]), "deleted": status == "D", "lines": None})
                continue
        out.append({"old": None, "new": git_unquote(line.strip()), "deleted": False, "lines": None})
    return out


def build_changed(raw_entries, roots, warnings):
    """Merge stdin and diff entries by new path; confine every path to the root."""
    merged, rejected = {}, []
    for entry in raw_entries:
        new, reason = normalize_path(entry["new"], roots) if entry["new"] else (None, "empty path")
        if new is not None and new.startswith("/"):
            new, reason = None, "outside the repository root"
        if new is None:
            rejected.append((entry["new"], reason))
            continue
        old = None
        if entry.get("old") and entry["old"] != entry["new"]:
            old, _ = normalize_path(entry["old"], roots)
            if old is not None and old.startswith("/"):
                old = None
        item = merged.setdefault(new, {"path": new, "old": None, "deleted": False, "lines": None})
        item["old"] = item["old"] or old
        item["deleted"] = item["deleted"] or entry["deleted"]
        if entry.get("lines") is not None:  # from a diff: line precision (possibly none, e.g. a pure rename)
            item["lines"] = (item["lines"] or set()) | entry["lines"]
    for text, reason in rejected:
        warnings.append(f"changed path rejected ({reason}): {clean(text)!r}")
    return [merged[k] for k in sorted(merged)], rejected


# ------------------------------------------------------------------------------------------ analysis

def blank_file(path, status, notes, old_path=None):
    return {
        "path": path, "old_path": old_path, "status": status, "granularity": "none",
        "executable_lines": 0, "covered_lines": 0, "uncovered_lines": 0, "line_coverage": None,
        "uncovered_ranges": [], "report_match": [], "covered_by": [], "covering_layers": [],
        "exclusive_lines": {}, "lines_by_layer": {}, "notes": notes,
    }


def analyse_file(item, reports, root, notes_for_stale):
    path = item["path"]
    result = blank_file(path, "", [], item["old"])
    if item["old"]:
        result["notes"].append(f"renamed from {item['old']}")
    suffix = posixpath.splitext(path)[1].lower()
    if item["deleted"]:
        result["status"] = "deleted"
        result["notes"].append("deleted: nothing left to cover")
        return result
    if is_test_path(path):
        result["status"] = "test_file"
        result["notes"].append("a test file: not measured against the report")
        return result
    if suffix not in CODE_SUFFIXES or path.lower().endswith(".d.ts"):
        result["status"] = "not_code"
        return result

    matches, ambiguous = [], []
    for report in reports:
        key, kind = report.find(path)
        if kind in ("exact", "suffix"):
            matches.append((report, key, kind))
            result["report_match"].append({"report": report.label, "path": key, "match": kind})
        elif kind == "ambiguous":
            ambiguous.append(report)
        elif item["old"]:
            old_key, old_kind = report.find(item["old"])
            if old_kind in ("exact", "suffix"):
                notes_for_stale.append(path)
                result["notes"].append(
                    f"report '{report.label}' knows only the old name {item['old']}: it predates the rename")
    for report in ambiguous:
        result["notes"].append(f"report '{report.label}': more than one report path matches this file; no claim made")
    if item["lines"] is not None and not item["lines"]:
        result["status"] = "no_executable_lines"
        result["notes"].append("the diff adds or modifies no lines here (rename, mode change or deletion only): "
                               "nothing new to cover")
        return result
    if not matches:
        result["status"] = "ambiguous" if ambiguous else "not_in_report"
        if not ambiguous:
            result["notes"].append(
                "no supplied report mentions this file: no test loaded it, or it is excluded from instrumentation "
                "(generated code, ExcludeByFile), or the report is the wrong one")
        return result

    executable = set()
    for report, key, _ in matches:
        executable |= set(report.lines.get(key, {}))
    if item["lines"] is None:
        result["granularity"] = "file"
        changed = set(executable)
    else:
        result["granularity"] = "lines"
        changed = item["lines"] & executable
        if not changed:
            result["notes"].append("changed lines are not instrumented (comments, declarations, usings)")
    result["executable_lines"] = len(changed)
    if not changed:
        result["status"] = "no_executable_lines"
        return result

    covered_by_layer = {}
    covered = set()
    for number in changed:
        layers = set()
        for report, key, _ in matches:
            layers |= report.layers_at(key, number)
        if layers:
            covered.add(number)
            covered_by_layer[number] = layers
    uncovered = changed - covered
    result["covered_lines"], result["uncovered_lines"] = len(covered), len(uncovered)
    result["line_coverage"] = round(len(covered) / len(changed), 4)
    result["uncovered_ranges"] = ranges(uncovered)
    result["status"] = "covered" if not uncovered else ("uncovered" if not covered else "partial")

    exclusive = {}
    for number, layers in covered_by_layer.items():
        if len(layers) == 1:
            only = next(iter(layers))
            exclusive[only] = exclusive.get(only, 0) + 1
    result["exclusive_lines"] = {k: exclusive[k] for k in LAYERS if k in exclusive}
    per_layer = {}
    for layers in covered_by_layer.values():
        for layer in layers:
            per_layer[layer] = per_layer.get(layer, 0) + 1
    result["lines_by_layer"] = {k: per_layer[k] for k in LAYERS if k in per_layer}
    result["covering_layers"] = [layer for layer in LAYERS if any(layer in v for v in covered_by_layer.values())]
    for report, key, _ in matches:
        hit_lines = [n for n in changed if report.layers_at(key, n)]
        if not hit_lines:
            continue
        layers = set()
        for n in hit_lines:
            layers |= report.layers_at(key, n)
        names = report.tests_at(key, hit_lines) if report.per_test_names else None
        result["covered_by"].append({
            "report": report.label, "layer": report.layer, "layers": [l for l in LAYERS if l in layers],
            "lines": len(hit_lines),
            "tests": sorted(n[:200] for n in names)[:SHOWN_TESTS] if names is not None else None,
            "tests_total": len(names) if names is not None else None,
        })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--report", action="append", required=True, metavar="[LABEL=]PATH",
                        help="Cobertura XML or lcov report; repeatable; LABEL names the suite or layer")
    parser.add_argument("--diff", help="unified diff of the change, for changed-line precision and renames")
    parser.add_argument("--root", default=".", help="repository root that changed paths are relative to")
    parser.add_argument("--json", action="store_true", help="machine-readable output (schema in the header)")
    parser.add_argument("--limits", action="store_true",
                        help="spell out what these numbers cannot tell you (always in --json)")
    args = parser.parse_args()

    root = args.root
    if not os.path.isdir(root):
        print(f"coverage-impact: --root is not a directory: {clean(root)}", file=sys.stderr)
        return 2
    roots = root_variants(root)

    try:
        reports = [load_report(spec, root, roots) for spec in args.report]
        raw = []
        if args.diff:
            if not os.path.isfile(args.diff):
                raise ReportError(f"diff not found: {clean(args.diff)}")
            if os.path.getsize(args.diff) > MAX_BYTES:
                raise ReportError("diff is too large")
            with open(args.diff, "rb") as handle:
                raw += [{"old": e["old"], "new": e["new"], "deleted": e["deleted"], "lines": e["lines"]}
                        for e in parse_diff(handle.read().decode("utf-8", errors="replace"))]
        if not (args.diff and sys.stdin.isatty()):
            if sys.stdin.isatty():
                raise ReportError("no changed paths: pipe them on stdin (git diff --name-only ...) or pass --diff")
            raw += parse_stdin(sys.stdin.read())
    except ReportError as error:
        print(f"coverage-impact: {error}", file=sys.stderr)
        return 2

    warnings = []
    changed, rejected = build_changed(raw, roots, warnings)
    stale_notes = []
    files = [analyse_file(item, reports, root, stale_notes) for item in changed]
    for text, reason in sorted(set((clean(t or "", 200), r) for t, r in rejected)):
        files.append(blank_file(text, "rejected", [f"rejected: {reason}; never opened"]))
    files.sort(key=lambda f: (f["status"] == "rejected", f["path"]))

    # A short report path (relative to a project folder) claimed by several changed files is not a safe match.
    claimed = {}
    for f in files:
        for m in f["report_match"]:
            if m["match"] == "suffix" and not m["path"].startswith("/"):
                claimed.setdefault((m["report"], m["path"]), []).append(f)
    for (label, key), owners in claimed.items():
        if len(owners) > 1:
            for f in owners:
                notes = f["notes"] + [f"report '{label}' path {key} fits several changed files; no claim made"]
                f.update(blank_file(f["path"], "ambiguous", notes, f["old_path"]))

    # Staleness: a changed file newer than the report that is supposed to describe it.
    stale_files, existing = [], 0
    for item in changed:
        mtime = None if item["deleted"] else safe_stat(root, item["path"])
        if mtime is None:
            continue
        existing += 1
        for report in reports:
            if report.generated_at is not None and mtime > report.generated_at + TOLERANCE_SECONDS:
                stale_files.append({"path": item["path"], "modified_at": iso(mtime), "report": report.label})
    if changed and not existing:
        warnings.append("none of the changed paths exist under the root: is --root right, or were they all deleted?")
    by_report = {}
    for entry in stale_files:
        by_report.setdefault(entry["report"], []).append(entry["path"])
    for label, paths in reversed(list(by_report.items())):
        report = next(r for r in reports if r.label == label)
        source = "report timestamp" if report.generated_source == "report" else "file mtime"
        warnings.insert(0, (
            f"STALE REPORT: '{label}' was generated {iso(report.generated_at)} ({source}), older than "
            f"{len(paths)} changed file(s), e.g. {clean(paths[0])}. Line numbers and coverage below may not "
            f"describe this code. Regenerate coverage on the current code (scripts/verify.sh, T.1) and rerun."))
    for path in sorted(set(stale_notes)):
        warnings.append(f"STALE REPORT: renamed file {clean(path)} appears in a report only under its old name")
    for report in reports:
        if not report.lines:
            warnings.append(f"report '{report.label}' contains no files: nothing can be shown covered by it")
        if report.ignored:
            warnings.append(f"report '{report.label}': {report.ignored} path(s) or line(s) ignored "
                            f"('..' component, control character, or malformed); they were not matched")
        if report.layer == "unknown":
            warnings.append(f"report '{report.label}': layer not inferable from its label or path; "
                            f"label it, e.g. --report unit={clean(report.path)}")
    supplied = [layer for layer in LAYERS if any(r.layer == layer for r in reports)]
    known = [layer for layer in supplied if layer != "unknown"]
    if len(known) < 2:
        warnings.append("only one layer supplied" + (f" ({known[0]})" if known else "") +
                        ": 'covered only by <layer>' cannot be told from 'only this layer was supplied'; "
                        "pass one report per layer (unit, integration, e2e) to see the spread")

    by_status, layer_lines, only_layer, only_files = {}, {}, {}, {}
    for f in files:
        by_status[f["status"]] = by_status.get(f["status"], 0) + 1
        for layer, n in f["lines_by_layer"].items():
            layer_lines[layer] = layer_lines.get(layer, 0) + n
        for layer, n in f["exclusive_lines"].items():
            only_layer[layer] = only_layer.get(layer, 0) + n
        if len(f["covering_layers"]) == 1:
            only_files.setdefault(f["covering_layers"][0], []).append(f["path"])
    exe = sum(f["executable_lines"] for f in files)
    cov = sum(f["covered_lines"] for f in files)
    granularities = {f["granularity"] for f in files} - {"none"}
    granularity = "none" if not granularities else (granularities.pop() if len(granularities) == 1 else "mixed")
    summary = {
        "granularity": granularity,
        "changed_files": len(files),
        "by_status": dict(sorted(by_status.items())),
        "executable_lines": exe, "covered_lines": cov, "uncovered_lines": exe - cov,
        "line_coverage": round(cov / exe, 4) if exe else None,
        "uncovered_files": [f["path"] for f in files
                            if f["status"] in ("not_in_report", "uncovered", "partial", "ambiguous")],
        "covered_lines_by_layer": {l: layer_lines[l] for l in LAYERS if l in layer_lines},
        "covered_only_by_layer": {l: only_layer[l] for l in LAYERS if l in only_layer},
        "files_covered_only_by": {l: sorted(only_files[l]) for l in LAYERS if l in only_files},
    }
    document = {
        "schema_version": SCHEMA_VERSION, "tool": "coverage-impact", "informational": True,
        "limits": LIMITS, "warnings": warnings, "root": roots[0], "show_limits": args.limits,
        "reports": [{
            "label": r.label, "path": r.path, "format": r.format, "layer": r.layer, "layer_basis": r.layer_basis,
            "generated_at": iso(r.generated_at), "generated_at_source": r.generated_source,
            "files": len(r.lines), "ignored_paths": r.ignored, "per_test_names": r.per_test_names,
        } for r in reports],
        "layers_supplied": supplied,
        "stale": {"checked": existing > 0, "is_stale": bool(stale_files or stale_notes), "files": stale_files,
                  "renamed_unknown_to_report": sorted(set(stale_notes))},
        "summary": summary,
        "files": files,
    }
    if args.json:
        print(json.dumps(document, indent=2, sort_keys=False, ensure_ascii=True))
    else:
        render(document)
    return 0


def render(doc):
    out = print
    s = doc["summary"]
    out("coverage-impact: which tests execute the changed code, and what is left uncovered")
    out("Informational, not a gate: it exits 0 whatever the number is, and sets no threshold. "
        "Executed is not asserted; --limits spells out what these numbers cannot tell you.")
    if doc.get("show_limits"):
        out(NO_THRESHOLD)
        for number, text in enumerate(LIMITS, 1):
            out(f"Limit {number}: {text}")
    out("")
    out("Reports")
    for r in doc["reports"]:
        basis = {"label": "from label", "path": "from path", "default": "assumed from a generic 'tests' name",
                 "none": "not inferable"}[r["layer_basis"]]
        when = f", generated {r['generated_at']} ({r['generated_at_source']})" if r["generated_at"] else ""
        out(f"  {clean(r['label'])}: {r['format']}, layer {r['layer']} ({basis}), {r['files']} file(s){when}")
    for w in doc["warnings"]:
        out(("WARNING: " if not w.startswith("STALE") else "") + clean(w, 600))
    out("")

    counts = s["by_status"]
    kinds = ", ".join(f"{n} {k}" for k, n in counts.items()) or "nothing"
    scope = {"lines": "changed lines (from --diff)", "file": "whole files (no --diff: numbers describe the file, not your change)",
             "mixed": "changed lines for files in --diff, whole file for the rest", "none": "n/a"}[s["granularity"]]
    out(f"Changed: {s['changed_files']} file(s): {kinds}. Measured on {scope}.")
    if s["executable_lines"]:
        pct = f"{s['line_coverage'] * 100:.1f}%"
        out(f"Executable lines in scope: {s['executable_lines']}; executed by a supplied report: {s['covered_lines']} "
            f"({pct}); not executed: {s['uncovered_lines']}. A number for the reviewer, not a verdict.")
    else:
        out("No instrumented lines in scope, so there is no coverage number.")
    out("")

    problem = [f for f in doc["files"] if f["status"] in ("not_in_report", "uncovered", "partial", "ambiguous")]
    out("NOT COVERED (what nothing in the supplied reports executes)" if problem else "NOT COVERED: nothing in scope")
    for f in problem:
        name = clean(f["path"])
        if f["status"] == "not_in_report":
            out(f"  {name}: NOT IN ANY REPORT. No supplied report mentions this file (no test loaded it, or it is "
                f"excluded from instrumentation, or the report is the wrong one).")
        elif f["status"] == "ambiguous":
            out(f"  {name}: AMBIGUOUS. {clean(f['notes'][-1], 300) if f['notes'] else 'several report paths match'}")
        else:
            out(f"  {name}: {f['uncovered_lines']} of {f['executable_lines']} executable line(s) not executed: "
                f"lines {fmt_ranges(f['uncovered_ranges'])}" + (" (all of them)" if f["status"] == "uncovered" else ""))
        for note in f["notes"]:
            if note.startswith("renamed") or "old name" in note:
                out(f"      {clean(note, 300)}")
    out("")

    covered = [f for f in doc["files"] if f["covered_lines"]]
    out("COVERED, BY WHICH TESTS AND LAYER" if covered else "COVERED: no changed line is executed by a supplied report")
    single = len([l for l in doc["layers_supplied"] if l != "unknown"]) < 2
    for f in covered:
        who = []
        for entry in f["covered_by"]:
            text = f"{clean(entry['report'])} [{'+'.join(entry['layers'])}]"
            if entry["tests"]:
                shown = ", ".join(clean(t, 80) for t in entry["tests"][:5])
                more = entry["tests_total"] - min(5, len(entry["tests"]))
                text += f" tests: {shown}" + (f" (+{more} more)" if more > 0 else "")
            who.append(text)
        only = ""
        if len(f["covering_layers"]) == 1 and f["covering_layers"][0] != "unit" and not single:
            only = f"  <- ONLY {f['covering_layers'][0]}: no other supplied layer executes it"
        out(f"  {clean(f['path'])}: {f['covered_lines']}/{f['executable_lines']} line(s) by {'; '.join(who)}{only}")
    if covered and doc["layers_supplied"]:
        out("  Layers: " + ", ".join(f"{l} {n} line(s)" for l, n in s["covered_lines_by_layer"].items())
            + ("; exclusively: " + ", ".join(f"{l} {n}" for l, n in s["covered_only_by_layer"].items())
               if s["covered_only_by_layer"] else ""))
    if any("e2e" == l for l in s["files_covered_only_by"]) and not single:
        out("  e2e-only coverage runs after deploy (T.3 layer 2), not in scripts/verify.sh: a defect here is found "
            "late, and T.4 asks for a layer 0 or 1 test.")
    out("")

    skipped = [f for f in doc["files"] if f["status"] in ("test_file", "not_code", "deleted", "rejected", "no_executable_lines")]
    for f in skipped:
        note = f["notes"][0] if f["notes"] else ""
        out(f"  {f['status']}: {clean(f['path'])}" + (f" ({clean(note, 200)})" if note else ""))
    if skipped:
        out("")
    out("Reading this: executed is not asserted. Covered lines may only be run incidentally by an unrelated test, "
        "and this tool cannot tell. Use the numbers to decide where to look, not as proof (T.1).")


if __name__ == "__main__":
    sys.exit(main())
