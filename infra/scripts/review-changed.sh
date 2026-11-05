#!/usr/bin/env bash
# Did this change touch what shapes the AI review (rules, playbooks, examples, templates, review tools)?
# Prints a yes/no line; in Azure DevOps it also sets EvalsNeeded=true. Usage: infra/scripts/review-changed.sh
set -euo pipefail

base="origin/${SYSTEM_PULLREQUEST_TARGETBRANCH:-refs/heads/main}"
base="${base/refs\/heads\//}"

pattern='^(AGENTS\.base\.md$|skills/|adapters/|harness/tvh$|harness/(rules|playbooks|examples|templates|hooks)/|harness/tools/(cli/|harness/(bundle|context)\.py$|review/|verification/))'
changed="$(git diff --name-only "$base"...HEAD)"
if grep -Eq "$pattern" <<<"$changed"; then
  echo "review inputs changed: the reviewer evals run"
  echo "##vso[task.setvariable variable=EvalsNeeded]true"
else
  echo "review inputs unchanged: the reviewer evals are skipped"
fi
