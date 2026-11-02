#!/usr/bin/env bash
# T.1 for a JavaScript or TypeScript project inside a repo whose verify command is otherwise .NET: install from the lockfile,
# then format check, build and test, each only if the project defines that script. A missing step is named, never skipped silently.
# Usage: node-verify.sh <project-dir>
# The package manager comes from the lockfile (bun.lock or bun.lockb, pnpm-lock.yaml, yarn.lock, package-lock.json). Installs are
# frozen, so a lockfile that does not match package.json fails here and not in CI.
set -euo pipefail

dir="${1:?usage: node-verify.sh <project-dir>}"
[[ -f "$dir/package.json" ]] || { echo "node-verify: $dir has no package.json" >&2; exit 1; }
cd "$dir"

if [[ -f bun.lock || -f bun.lockb ]]; then
  pm=bun; install=(install --frozen-lockfile); run=(run)
elif [[ -f pnpm-lock.yaml ]]; then
  pm=pnpm; install=(install --frozen-lockfile); run=(run)
elif [[ -f yarn.lock ]]; then
  pm=yarn; install=(install --frozen-lockfile); run=(run)
elif [[ -f package-lock.json ]]; then
  pm=npm; install=(ci); run=(run)
else
  echo "node-verify: $dir has no lockfile; commit one so installs are frozen (T.1)" >&2
  exit 1
fi
command -v "$pm" >/dev/null || { echo "node-verify: $pm not found; $dir NOT verified" >&2; exit 1; }

has_script() { jq -e --arg s "$1" '.scripts[$s] // empty' package.json >/dev/null 2>&1; }

echo "node-verify: $dir ($pm)"
"$pm" "${install[@]}" >/dev/null
for step in format:check lint build test; do
  if has_script "$step"; then
    "$pm" "${run[@]}" "$step"
  else
    echo "node-verify: $dir has no '$step' script; that step did not run" >&2
  fi
done
