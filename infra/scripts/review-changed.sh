#!/usr/bin/env bash
# Did this change touch what shapes the AI review (rules, playbooks, examples, templates, review tools)?
# Prints a yes/no line; in Azure DevOps it also sets EvalsNeeded=true. Usage: infra/scripts/review-changed.sh
set -euo pipefail

base="origin/${SYSTEM_PULLREQUEST_TARGETBRANCH:-refs/heads/main}"
base="${base/refs\/heads\//}"

pattern='^(harness/(rules|playbooks|examples|templates)/|harness/tools/(review/(review\.sh|eval\.py|run-claude\.py|thresholds\.json)|harness/bundle\.py))'
if git diff --name-only "$base"...HEAD | grep -Eq "$pattern"; then
  echo "review inputs changed: the reviewer evals run"
  echo "##vso[task.setvariable variable=EvalsNeeded]true"
else
  echo "review inputs unchanged: the reviewer evals are skipped"
fi
