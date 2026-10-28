#!/usr/bin/env bash
# The always-loaded text stays within its budget, and a PR may not raise the budget above the target branch's
# unless AllowContextGrowth=true. Usage: scripts/check-context-budget.sh   (CI or local; target defaults to main)
set -euo pipefail

bundle=harness/tools/harness/bundle.py
budget_file=harness/tools/harness/context-budget.json

python3 -I "$bundle" budget

base="origin/${SYSTEM_PULLREQUEST_TARGETBRANCH:-refs/heads/main}"
base="${base/refs\/heads\//}"
if [ "${AllowContextGrowth:-false}" = "true" ] || ! git cat-file -e "$base:$budget_file" 2>/dev/null; then
  exit 0
fi

baseline="$(mktemp)"
trap 'rm -f "$baseline"' EXIT
git show "$base:$budget_file" >"$baseline"
python3 -I "$bundle" budget --baseline "$baseline"
