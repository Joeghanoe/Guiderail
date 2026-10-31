#!/usr/bin/env python3
"""IAC.9: services listen on both IP families, and container probes use 127.0.0.1.

Usage: check-dual-stack.py [directory]    (default: the current directory)
Reads files only. Prints `path:line: IAC.9 message` per finding; exit 1 when there is one, 0 otherwise.
A deliberate exception carries `dual-stack: ok - <reason>` on the same line.
"""
import pathlib
import re
import sys

SKIP = {"bin", "obj", ".git", ".harness", "node_modules", "dist", "build", "out", "__pycache__", ".venv"}
SUFFIXES = {".cs", ".json", ".yml", ".yaml", ".conf", ".template", ".sh", ".toml"}
MAX_BYTES = 512 * 1024
EXEMPT = re.compile(r"dual-stack:\s*ok", re.I)

# (pattern, message). Each runs on one line.
LINE_RULES = [
    (re.compile(r"http://0\.0\.0\.0:", re.I),
     "binds IPv4 only; use http://[::]:PORT (or http://+:PORT) so the service is reachable on an IPv6-only private network"),
    (re.compile(r"\b(?:HOST|ASPNETCORE_URLS|BIND_ADDRESS)\b[\"']?\s*[:=]\s*[\"']?(?:http://)?0\.0\.0\.0\b", re.I),
     "binds IPv4 only; use HOST=:: (dual-stack)"),
    (re.compile(r"--host[ =]0\.0\.0\.0|(?<![\w.])-H[ =]0\.0\.0\.0|-b[ =]0\.0\.0\.0", re.I),
     "binds IPv4 only; use --host :: (or -b [::]:PORT)"),
    (re.compile(r"\.listen\([^)]*['\"]0\.0\.0\.0['\"]", re.I), "binds IPv4 only; listen on '::' (dual-stack)"),
    (re.compile(r"\bhost\s*=\s*['\"]0\.0\.0\.0['\"]", re.I), "binds IPv4 only; use host='::' (dual-stack)"),
]
# A probe line mentions a probing tool or key and the name localhost.
PROBE = re.compile(r"(?:healthcheck|test:|wget|curl|nc\b|probe)[^\n]*\blocalhost\b", re.I)
PROBE_MESSAGE = "the health probe calls localhost, which can resolve to ::1 and fail against an IPv4-only listener; call 127.0.0.1"
NGINX_V4 = re.compile(r"^\s*listen\s+(?!\[::\])[^;\[]*;", re.M)
NGINX_V6 = re.compile(r"^\s*listen\s+\[::\]", re.M)


def candidates(root):
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if SKIP & set(rel.parts) or path.is_symlink() or not path.is_file():
            continue
        if path.suffix in SUFFIXES or path.name.lower().startswith("dockerfile"):
            yield rel, path


def read(path):
    try:
        if path.stat().st_size > MAX_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def scan(root):
    findings = []
    for rel, path in candidates(root):
        body = read(path)
        lines = body.splitlines()
        for number, line in enumerate(lines, 1):
            if EXEMPT.search(line):
                continue
            for pattern, message in LINE_RULES:
                if pattern.search(line):
                    findings.append(f"{rel.as_posix()}:{number}: IAC.9 {message}")
            if PROBE.search(line) and ("healthcheck" in line.lower() or "test" in line.lower() or path.name.lower().startswith("dockerfile")
                                       or path.suffix in {".yml", ".yaml", ".json"}):
                findings.append(f"{rel.as_posix()}:{number}: IAC.9 {PROBE_MESSAGE}")
        # nginx: an IPv4 listen with no [::] listen anywhere in the same file
        if path.suffix in {".conf", ".template"} and NGINX_V4.search(body) and not NGINX_V6.search(body):
            first = next(i for i, l in enumerate(lines, 1) if NGINX_V4.match(l) and not EXEMPT.search(l))
            findings.append(f"{rel.as_posix()}:{first}: IAC.9 nginx listens on IPv4 only; add `listen [::]:PORT;`")
    return findings


def main(argv):
    root = pathlib.Path(argv[1] if len(argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"check-dual-stack: {root} is not a directory", file=sys.stderr)
        return 1
    findings = scan(root)
    for line in findings:
        print(line)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
