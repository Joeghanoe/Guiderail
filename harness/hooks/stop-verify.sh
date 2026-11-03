#!/usr/bin/env bash
# Stop hook (T.1): before the agent reports done, run the project's quick verify, kept outside the repo in
# ~/.golden-path-harness/projects/<repo-id>/verify.sh (see tools/code/project-verify.sh). CI runs the full gate. A scripts/verify.sh
# committed in the repo is not used. Exit 2 sends the agent back to work.
# Skipped when the project has no verify, and on the second stop attempt so it cannot loop.
set -euo pipefail

input="$(cat)"
[[ "$(jq -r '.stop_hook_active // false' <<<"$input")" == "true" ]] && exit 0

root="${CLAUDE_PROJECT_DIR:-$(pwd)}"
verify="$(bash "$(dirname "${BASH_SOURCE[0]}")/../tools/code/project-verify.sh" path "$root")"
[[ -x "$verify" ]] || exit 0

# Only verify when something changed; a question-and-answer session needs no build.
if git -C "$root" diff --quiet HEAD -- 2>/dev/null && [[ -z "$(git -C "$root" ls-files --others --exclude-standard 2>/dev/null)" ]]; then
  exit 0
fi

if ! out="$(cd "$root" && HARNESS_REPO_ROOT="$root" "$verify" --fast 2>&1)"; then
  echo "$verify --fast failed (T.1). Fix it, or tell the user exactly what fails and why:" >&2
  tail -n 40 <<<"$out" >&2
  exit 2
fi
exit 0
