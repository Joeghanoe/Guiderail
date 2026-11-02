#!/usr/bin/env bash
# Show why an Azure DevOps pipeline run failed: the run, the failed stage/job/task records, their error
# issues and the tail of each failed task's log. Replaces clicking through the run page.
#
# Tool contract (Vegviser AI Tool Boundary)
#   Classification:  Read. GET only, fixed host (dev.azure.com), three build endpoints.
#   Owner:           team:teamvalue-aicoe. Version: the harness commit in .harness/VERSION.
#   Caller identity: the user's own `az` login (or HARNESS_AZURE_CONFIG_DIR). The token is requested here for
#                    the Azure DevOps resource only, passed to curl on stdin, and never printed. The agent
#                    never logs in (CLD.1).
#   Inputs:          <organization> <project> <runId> [tail-lines, default 80]. runId is the numeric id
#                    (`cloud-read.sh az pipelines runs list ... --query "[0].id"`), not the build number.
#   Results:         plain text on stdout; exit 3 with a reason when refused; exit 4 on HTTP >= 400.
#   Side effects:    none. Log text is untrusted data (SEC.1) and is redacted for obvious secrets (SEC.2); the
#                    redaction is best effort, so a human still reads before pasting a log elsewhere.
#   Review trigger:  a new endpoint, or any endpoint that returns variables, secure files or connections.
#
# Why not cloud-read.sh: the Azure DevOps CLI has no log command, and `az devops invoke` is refused there
# because the verb can also write. This script exposes the three reads that are needed and nothing else.
#
# Usage:   ado-run-failure.sh https://dev.azure.com/teamvalue Bizure 26122
set -euo pipefail

tool="ado-run-failure"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=ado-common.sh
source "$here/ado-common.sh"

[[ $# -ge 3 ]] || ado_refuse "usage: ado-run-failure.sh <organization-url> <project> <runId> [tail-lines]"
run_id="$3"
tail_lines="${4:-80}"

[[ "$run_id" =~ ^[0-9]+$ ]] || ado_refuse "runId must be the numeric run id, not the build number."
[[ "$tail_lines" =~ ^[0-9]+$ ]] || ado_refuse "tail-lines must be a number."
((tail_lines <= 400)) || ado_refuse "tail-lines above 400 would put too much untrusted text in context."

ado_init "$1" "$2"
base="$ado_org/$ado_project/_apis/build/builds/$run_id"
get() { ado_get "$@"; }

redact() {
  sed -E \
    -e 's/\x1b\[[0-9;]*[A-Za-z]//g' \
    -e 's/^[0-9T:.Z-]+ //' \
    -e 's/(password|passwd|pwd|secret|token|apikey|api-key|accountkey|sharedaccesskey|sig)([=:"'"'"' ]+)[^ "'"'"';&]+/\1\2***/Ig' \
    -e 's/(Bearer|Basic) [A-Za-z0-9._~+\/=-]+/\1 ***/g' \
    -e 's/eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]*/***jwt***/g'
}

run="$(get "$base?api-version=7.1")"
jq -r '"Run \(.buildNumber) (id \(.id)): \(.result // .status)
Pipeline: \(.definition.name)  Reason: \(.reason)
Branch: \(.sourceBranch)  Commit: \(.sourceVersion)
Queued: \(.queueTime)  Finished: \(.finishTime // "not finished")"' <<<"$run"

timeline="$(get "$base/timeline?api-version=7.1")"

echo
echo "== Failed records (stage > job > task)"
jq -r '
  . as $t | .records as $r
  | def name($id): ($r[] | select(.id == $id) | .name) // empty;
  [ $r[] | select(.result == "failed") ]
  | if length == 0 then "none: no record has result failed (cancelled, skipped or still running)"
    else .[] | "\(.type)\t\([ .parentId | select(. != null) | name(.) ] | join("")) > \(.name)\t\(.errorCount) error(s)" end' <<<"$timeline"

echo
echo "== Error issues"
jq -r '
  [ .records[] | select(.result == "failed") | .name as $n | (.issues // [])[] | select(.type == "error") | "[\($n)] \(.message)" ]
  | unique | .[]' <<<"$timeline" | redact | head -n 60

while IFS=$'\t' read -r log_id task_name; do
  [[ -n "$log_id" ]] || continue
  echo
  echo "== Last $tail_lines lines of log for task: $task_name"
  get "$base/logs/$log_id?api-version=7.1" | tail -n "$tail_lines" | redact
done < <(jq -r '.records[] | select(.result == "failed" and .type == "Task" and .log != null) | "\(.log.id)\t\(.name)"' <<<"$timeline")
