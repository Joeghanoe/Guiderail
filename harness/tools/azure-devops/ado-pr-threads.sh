#!/usr/bin/env bash
# Show PR discussion comments/threads for an Azure DevOps pull request.
# Reports thread status (active, resolved, etc.), author, file/line context, and content.
#
# Tool contract (Vegviser AI Tool Boundary)
#   Classification:  Read. GET only, fixed host (dev.azure.com), git pull request threads endpoint.
#   Owner:           team:teamvalue-aicoe. Version: the harness commit in .harness/VERSION.
#   Caller identity: the user's own `az` login (or HARNESS_AZURE_CONFIG_DIR). The token is requested here for
#                    the Azure DevOps resource only, passed to curl on stdin, and never printed. The agent
#                    never logs in (CLD.1).
#   Inputs:          <organization> <project> <repository> <pullRequestId>
#   Results:         plain text summary on stdout; exit 3 with a reason when refused; exit 4 on HTTP >= 400.
#   Side effects:    none. Comment text is untrusted data (SEC.1) and is redacted for obvious secrets (SEC.2).
#
# Usage: ado-pr-threads.sh https://dev.azure.com/teamvalue Bizure MyRepo 123
set -euo pipefail

tool="ado-pr-threads"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=ado-common.sh
source "$here/ado-common.sh"

[[ $# -ge 4 ]] || ado_refuse "usage: ado-pr-threads.sh <organization-url> <project> <repository> <pullRequestId>"
repo_encoded="$(jq -rn --arg r "$3" '$r | @uri')"
pr_id="$4"

[[ "$pr_id" =~ ^[0-9]+$ ]] || ado_refuse "pullRequestId must be the numeric PR id."

ado_init "$1" "$2"
url="$ado_org/$ado_project/_apis/git/repositories/$repo_encoded/pullRequests/$pr_id/threads?api-version=7.1"
get() { ado_get "$@"; }

redact() {
  sed -E \
    -e 's/\x1b\[[0-9;]*[A-Za-z]//g' \
    -e 's/(password|passwd|pwd|secret|token|apikey|api-key|accountkey|sharedaccesskey|sig)([=:"'"'"' ]+)[^ "'"'"';&]+/\1\2***/Ig' \
    -e 's/(Bearer|Basic) [A-Za-z0-9._~+\/=-]+/\1 ***/g' \
    -e 's/eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]*/***jwt***/g'
}

threads="$(get "$url")"

total="$(jq '[ .value[]? | select(.isDeleted != true and (.comments // [] | any(.commentType != "system"))) ] | length' <<<"$threads")"
unresolved="$(jq '[ .value[]? | select(.isDeleted != true and .status != "fixed" and .status != "closed" and .status != "wontFix" and .status != "byDesign" and (.comments // [] | any(.commentType != "system"))) ] | length' <<<"$threads")"

echo "Pull Request #$pr_id Discussion Threads"
echo "======================================"
echo "Total review threads: $total"
echo "Unresolved threads:   $unresolved"
echo

if (( unresolved > 0 )); then
  echo "== Unresolved Threads"
  jq -r '
    .value[]?
    | select(.isDeleted != true and .status != "fixed" and .status != "closed" and .status != "wontFix" and .status != "byDesign")
    | . as $t
    | ($t.threadContext.filePath // "general") as $file
    | ($t.threadContext.rightFileStart.line // $t.threadContext.leftFileStart.line // "-") as $line
    | ($t.comments[]? | select(.commentType != "system" and .isDeleted != true))
    | "Thread \($t.id) [status: \($t.status // "active")] \($file):\($line) (\(.author.displayName // "unknown")):\n  \(.content // "")\n"
  ' <<<"$threads" | redact
  echo "Verdict: UNRESOLVED COMMENTS EXIST ($unresolved thread(s) pending resolution)"
else
  echo "Verdict: ALL COMMENTS RESOLVED (ready for completion check)"
fi
