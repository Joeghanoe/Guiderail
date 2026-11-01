#!/usr/bin/env bash
# PreToolUse hook for Edit|Write|NotebookEdit (H.2). Denies the first edit of a session until the rule lookup has run,
# then puts the matching rule summaries and linked examples in front of the agent once per file type.
# guard-bash.sh writes the session marker when it sees `bundle.py select`. Fails open without a session id or bundle.py.
set -euo pipefail

input="$(cat)"
sid="$(jq -r '.session_id // ""' <<<"$input")"
file="$(jq -r '.tool_input.file_path // .tool_input.notebook_path // ""' <<<"$input")"
[[ -z "$sid" || -z "$file" ]] && exit 0

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bundle="$here/../tools/harness/bundle.py"
[[ -f "$bundle" ]] || exit 0

state="${TMPDIR:-/tmp}/golden-path-harness-lookup/${sid//[^A-Za-z0-9_-]/_}"
mkdir -p "$state"

if [[ ! -e "$state/selected" ]]; then
  echo "BLOCKED by harness (H.2 edit gate): look up the rules before editing. Run:" >&2
  echo "  python3 $bundle select --brief --examples \"$file\"" >&2
  exit 2
fi

ext="${file##*/}"; ext="${ext##*.}"
[[ -e "$state/ext-$ext" ]] && exit 0
touch "$state/ext-$ext"
ctx="$(python3 -I "$bundle" select --brief --examples "$file" 2>/dev/null || true)"
[[ -z "$ctx" ]] && exit 0
jq -n --arg c "Rules and examples for .$ext files (H.2):"$'\n'"$ctx" \
  '{hookSpecificOutput: {hookEventName: "PreToolUse", additionalContext: $c}}'
