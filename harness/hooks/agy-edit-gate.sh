#!/usr/bin/env bash
# Antigravity CLI (agy) PreToolUse hook: the H.2 edit gate (see edit-gate.sh for the Claude Code form).
# agy sends camelCase JSON on stdin and expects a JSON decision on stdout. Matcher: run_command|edit_file|write_file.
#   run_command with `bundle.py select` marks the conversation as looked up.
#   edit_file / write_file are denied until it is marked, and once per file type the rules and examples come back as the reason.
set -euo pipefail

input="$(cat)"
allow() { echo '{"decision":"allow"}'; exit 0; }
deny() { jq -n --arg r "$1" '{decision: "deny", reason: $r}'; exit 0; }

sid="$(jq -r '.conversationId // ""' <<<"$input")"
tool="$(jq -r '.toolCall.name // ""' <<<"$input")"
[[ -z "$sid" ]] && allow

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bundle="$(cd "$here/../tools/harness" 2>/dev/null && pwd -P)/bundle.py"
[[ -f "$bundle" ]] || allow
state="${TMPDIR:-/tmp}/golden-path-harness-lookup/agy-${sid//[^A-Za-z0-9_-]/_}"
mkdir -p "$state"

# agy may hand string arguments over still JSON-quoted; strip one layer of surrounding quotes.
arg() { jq -r --arg k "$1" '.toolCall.args[$k] // "" | if type == "string" then (. as $s | try fromjson catch $s) else . end | tostring' <<<"$input"; }

case "$tool" in
  run_command)
    cmdline="$(arg CommandLine)"
    if grep -Eq '^python3 (-I )?[^;&|`$]*bundle\.py[[:space:]]+select([[:space:]]|$)[^;&|`$]*$' <<<"$cmdline"; then
      touch "$state/selected"   # the lookup is read-only; approve it so headless runs can follow the denial message
      jq -n --arg c "$cmdline" '{decision: "allow", permissionOverrides: ["command(" + $c + ")"]}'; exit 0
    fi
    allow ;;
  edit_file | write_file)
    file="$(arg Path)"; [[ -z "$file" ]] && file="$(arg TargetFile)"
    [[ -z "$file" ]] && allow
    [[ -e "$state/selected" ]] || deny "H.2 edit gate: look up the rules before editing. Run: python3 $bundle select --brief --examples \"$file\" , then retry the edit."
    ext="${file##*/}"; ext="${ext##*.}"
    [[ -e "$state/ext-$ext" ]] && allow
    touch "$state/ext-$ext"
    ctx="$(python3 -I "$bundle" select --brief --examples "$file" 2>/dev/null || true)"
    [[ -z "$ctx" ]] && allow
    deny "H.2: rules and examples for .$ext files. Read them, then retry the same edit."$'\n'"$ctx" ;;
  *) allow ;;
esac
