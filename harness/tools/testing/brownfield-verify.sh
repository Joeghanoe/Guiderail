#!/usr/bin/env bash
# Stand-in scripts/verify.sh for brownfield runs with hooks on (T.1, T.2, T.5).
# Real repos bring their own build and tests; a snapshot cannot, so this checks what it can see: a change to C#
# code comes with a changed test file, and every public or internal method the change adds is named in one.
# Naming a method is not proof it is asserted (see coverage-impact.py); it only rules out tests that skip the new code.
# Exit 1 sends the Stop hook's agent back to work.
set -euo pipefail

[[ "${1:-}" == "--design" ]] && exit 0
cd "$(git rev-parse --show-toplevel)"
changed="$({ git diff --name-only HEAD --; git ls-files --others --exclude-standard; } | sort -u)"
code="$(grep -E '\.cs$' <<<"$changed" | grep -viE '(tests?|\.harness)/|tests?\.cs$' || true)"
tests="$(grep -iE '(tests?/.*\.cs|tests?\.cs)$' <<<"$changed" || true)"

if [[ -n "$code" && -z "$tests" ]]; then
  echo "verify: C# code changed but no test file was added or changed (T.2, T.5, T.1)." >&2
  echo "Add a test beside the code (for example <Name>Tests.cs with a stub handler) covering the new behaviour." >&2
  exit 1
fi

if [[ -n "$code" ]]; then
  missing="$(python3 - $'\n'"$code" $'\n'"$tests" <<'PY'
import re
import subprocess
import sys

code = sys.argv[1].split()
tests = sys.argv[2].split()
body = "\n".join(open(t, encoding="utf-8", errors="replace").read() for t in tests)
declaration = re.compile(r"^\+\s*(?:public|internal)\s+(?:static\s+|async\s+|override\s+|virtual\s+)*[\w<>\[\]?,.]+\s+(\w+)\s*\(")
names = set()
for path in code:
    diff = subprocess.run(["git", "diff", "-U0", "HEAD", "--", path], capture_output=True, text=True).stdout
    if not diff:  # untracked: the whole file is new
        diff = "\n".join("+" + line for line in open(path, encoding="utf-8", errors="replace").read().splitlines())
    names.update(m.group(1) for line in diff.splitlines() if (m := declaration.match(line)))
print(" ".join(sorted(n for n in names if n not in body)))
PY
)"
  if [[ -n "$missing" ]]; then
    echo "verify: these new methods are not referenced by any changed test: $missing (T.5)." >&2
    echo "Add or extend a test that calls them, with a stub for the HTTP handler or other I/O (T.2)." >&2
    exit 1
  fi
fi
echo "verify: ok"
