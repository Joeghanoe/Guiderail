#!/usr/bin/env bash
# PreToolUse hook for Read/Grep/Glob. Blocks .env files (SEC.2); .env.example is allowed.
set -euo pipefail

input="$(cat)"
targets="$(jq -r '[.tool_input.file_path, .tool_input.path, .tool_input.pattern, .tool_input.glob] | map(select(. != null)) | .[]' <<<"$input")"

while IFS= read -r t; do
  [[ -z "$t" ]] && continue
  base="${t##*/}"
  if [[ "$base" == ".env" || ("$base" == .env.* && "$base" != ".env.example") || "$base" == *.env ]]; then
    echo "BLOCKED by harness (SEC.2): .env files are never read. Use .env.example for the structure." >&2
    exit 2
  fi
done <<<"$targets"

exit 0
