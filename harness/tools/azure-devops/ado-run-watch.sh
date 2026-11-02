#!/usr/bin/env bash
# Follow an Azure DevOps pipeline run until it ends. Prints one line when a stage, a job or a task changes
# state (and for failed or warning tasks), then a last line with the result. Meant for the Monitor tool: each
# stdout line is an event.
#
# Tool contract (Vegviser AI Tool Boundary)
#   Classification:  Read. GET only, fixed host (dev.azure.com), the build and timeline endpoints.
#   Owner:           team:teamvalue-aicoe. Version: the harness commit in .harness/VERSION.
#   Caller identity: the user's own `az` login, see ado-common.sh. The agent never logs in (CLD.1).
#   Inputs:          <organization> <project> <runId | latest:<branch>> [interval-seconds=30] [max-minutes=60].
#                    latest:<branch> takes the newest run of that branch at the moment of the call.
#   Results:         event lines on stdout. Exit 0 succeeded, 1 failed/cancelled/partially succeeded, 2 still
#                    running at max-minutes, 3 refused, 4 HTTP >= 400.
#   Side effects:    none. Task names come from the pipeline definition, not from log text.
#   Review trigger:  a new endpoint, or any endpoint that returns variables, secure files or connections.
#
# Usage:   ado-run-watch.sh https://dev.azure.com/teamvalue Bizure latest:feat/release-1.0
# After a failed end: ado-run-failure.sh <same org and project> <runId>
set -euo pipefail

tool="ado-run-watch"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=ado-common.sh
source "$here/ado-common.sh"

[[ $# -ge 3 ]] || ado_refuse "usage: ado-run-watch.sh <organization-url> <project> <runId|latest:branch> [interval-seconds] [max-minutes]"
interval="${4:-30}"
max_minutes="${5:-60}"
[[ "$interval" =~ ^[0-9]+$ && "$max_minutes" =~ ^[0-9]+$ ]] || ado_refuse "interval and max-minutes must be numbers."
((interval >= 10)) || ado_refuse "interval below 10 seconds only hammers the API."
((max_minutes <= 240)) || ado_refuse "max-minutes above 240; start a new watch instead."

ado_init "$1" "$2"
target="$3"
builds="$ado_org/$ado_project/_apis/build/builds"

if [[ "$target" == latest:* ]]; then
  branch="${target#latest:}"
  [[ "$branch" =~ ^[A-Za-z0-9._/-]+$ ]] || ado_refuse "branch has characters outside A-Za-z0-9._/-."
  run_id="$(ado_get "$builds?branchName=refs/heads/$branch&queryOrder=queueTimeDescending&\$top=1&api-version=7.1" | jq -r '.value[0].id // empty')"
  [[ -n "$run_id" ]] || ado_refuse "no run found for branch $branch."
else
  [[ "$target" =~ ^[0-9]+$ ]] || ado_refuse "run must be the numeric run id or latest:<branch>."
  run_id="$target"
fi

prev="$(mktemp)"
cur="$(mktemp)"
trap 'rm -f "$prev" "$cur"' EXIT
deadline=$((SECONDS + max_minutes * 60))
polls=0

stamp() { date +%H:%M:%S; }

while :; do
  # Refresh the token every 40 polls at most; one poll is two GETs.
  if ((polls > 0 && polls % 40 == 0)); then ado_token; fi
  polls=$((polls + 1))

  run="$(ado_get "$builds/$run_id?api-version=7.1")"
  if ((polls == 1)); then
    jq -r '"\(.buildNumber) (id \(.id)) on \(.sourceBranch) at \(.sourceVersion[0:7]): \(.status)"' <<<"$run" | sed "s/^/$(stamp) WATCHING /"
  fi

  ado_get "$builds/$run_id/timeline?api-version=7.1" | jq -r '
    .records[]?
    | select(.type == "Stage" or .type == "Job"
        or (.type == "Task" and (.state == "inProgress" or ((.result // "") | IN("failed", "succeededWithIssues", "canceled")))))
    | "\(.id)\t\(.type)\t\(.name)\t\(.state)/\(.result // "-")"' >"$cur"

  # Lines that were not in the previous snapshot are the changes; ids stay out of the output.
  grep -vxFf "$prev" "$cur" | cut -f2- | while IFS=$'\t' read -r type name state; do
    echo "$(stamp) $type '$name': $state"
  done || true
  cp "$cur" "$prev"

  status="$(jq -r '.status' <<<"$run")"
  if [[ "$status" == "completed" ]]; then
    result="$(jq -r '.result' <<<"$run")"
    echo "$(stamp) DONE run $run_id: $result"
    if [[ "$result" == "succeeded" ]]; then
      exit 0
    fi
    echo "$(stamp) NEXT ado-run-failure.sh ${1%/} $2 $run_id"
    exit 1
  fi
  if ((SECONDS >= deadline)); then
    echo "$(stamp) TIMEOUT run $run_id still $status after $max_minutes minutes"
    exit 2
  fi
  sleep "$interval"
done
