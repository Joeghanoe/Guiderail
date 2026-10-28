#!/usr/bin/env bash
# Verify that the harness rules are in an agent's context, not just referenced (Vegviser tool adapter contract).
# One short prompt, no tools: the agent must find the marker `tvh-loaded` in what it was given, not in a file.
#
# Usage:  check-adapter.sh [dir]     run in a repo (project adapter) or any other folder (global install)
# Output: one line to record in the harness README: tool, version, folder, result, date. Exit 1 when missing.
set -euo pipefail

dir="$(cd "${1:-.}" && pwd)"
version="$(claude --version 2>/dev/null | head -n 1)"
answer="$(cd "$dir" && claude -p "Do not use any tools and do not read files. Reply with exactly LOADED if the text tvh-loaded appears in the instructions you were given, otherwise exactly MISSING." \
  --max-turns 1 --output-format json 2>/dev/null | jq -r '.result // ""')"

result="missing"
[[ "$answer" == *LOADED* ]] && result="loaded"
echo "claude-code ${version:-unknown} | $dir | $result | $(date -u +%Y-%m-%d)"
[[ "$result" == "loaded" ]]
