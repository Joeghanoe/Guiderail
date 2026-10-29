#!/usr/bin/env bash
# Create the evaluation folder for same-user runs and print the one-time login steps.
# The folder gives agents their own HOME and config, so your personal tool config and logins are not used.
# It is not isolation: the agent still runs as you. Keep reference solutions and source PDFs off this machine.
set -euo pipefail

# Legacy ~/.harness-evaluation is kept when it already exists (its logins live there).
gp="${GOLDEN_PATH_HOME:-$HOME/.golden-path-harness}"
legacy="$HOME/.harness-evaluation"
if [[ -d "$legacy" ]]; then default="$legacy"; else default="$gp/evaluation"; fi
root="${HARNESS_EVAL_HOME:-$default}"
mkdir -p "$root"/{home,claude,codex,frozen,runs}
chmod 700 "$root"

for tool in python3 git dotnet claude codex; do
  command -v "$tool" >/dev/null || echo "missing: $tool"
done
dotnet --version 2>/dev/null | grep -q '^10\.' || echo "warning: .NET SDK 10 is required for the candidate and CODE.5"

cat <<MSG
Evaluation folder: $root
  home/    HOME for the agent        claude/  CLAUDE_CONFIG_DIR        codex/  CODEX_HOME
  frozen/  frozen packages (keep the manifest hash elsewhere)           runs/   run evidence

One-time subscription logins (separate from your personal ones):
  HOME="$root/home" CLAUDE_CONFIG_DIR="$root/claude" claude    # then /login
  HOME="$root/home" CODEX_HOME="$root/codex" codex login

Profile env to use:
  "env": {"HOME": "$root/home", "CLAUDE_CONFIG_DIR": "$root/claude", "CODEX_HOME": "$root/codex"}
MSG
