#!/usr/bin/env bash
# Post validated review findings (output of `bundle.py findings`) as Azure DevOps PR threads.
# Runs in a pipeline only: it needs SYSTEM_ACCESSTOKEN, and the build service needs "Contribute to pull requests".
# A finding that already has a thread (same rule, file and line) is not posted again, so reruns do not spam.
# The thread status a human sets (fixed, wontFix, byDesign) is the harness's feedback (H.1).
#
# Usage: ado-post-findings.sh <findings.json>
set -euo pipefail

findings="${1:?usage: ado-post-findings.sh <findings.json>}"
: "${SYSTEM_ACCESSTOKEN:?map SYSTEM_ACCESSTOKEN: \$(System.AccessToken) in the step env}"
: "${SYSTEM_COLLECTIONURI:?}" "${SYSTEM_TEAMPROJECT:?}" "${BUILD_REPOSITORY_ID:?}" "${SYSTEM_PULLREQUEST_PULLREQUESTID:?}"

project="$(jq -rn --arg p "$SYSTEM_TEAMPROJECT" '$p | @uri')"
api="${SYSTEM_COLLECTIONURI%/}/$project/_apis/git/repositories/$BUILD_REPOSITORY_ID/pullRequests/$SYSTEM_PULLREQUEST_PULLREQUESTID/threads"
auth=(-H "Authorization: Bearer $SYSTEM_ACCESSTOKEN" -H "Content-Type: application/json")

existing="$(curl -sSf "${auth[@]}" "$api?api-version=7.1" | jq -r '.value[].comments[]?.content // ""' | grep -o 'harness:[^ ]* ' || true)"

posted=0
while IFS= read -r f; do
  marker="harness:$(jq -r '"\(.rule_id):\(.file):\(.line)"' <<<"$f") "
  if grep -qF "$marker" <<<"$existing"; then
    continue
  fi
  body="$(jq -n --argjson f "$f" --arg marker "$marker" '{
    comments: [{
      parentCommentId: 0,
      commentType: 1,
      content: ("**\($f.rule_id) \($f.summary)** (\($f.severity), confidence \($f.confidence))\n\n"
        + "Evidence: `\($f.evidence)`\n\n"
        + (if ($f.fix // "") != "" then "Fix direction: \($f.fix)\n\n" else "" end)
        + (if ($f.not_verified // "") != "" then "Not verified: \($f.not_verified)\n\n" else "" end)
        + "_Proposed by the harness reviewer. Resolve as Fixed, Won'"'"'t fix or By design; that status is feedback for the harness._\n\n"
        + "<!-- \($marker)-->")
    }],
    status: 1,
    threadContext: {
      filePath: ("/" + ($f.file | ltrimstr("/"))),
      rightFileStart: { line: $f.line, offset: 1 },
      rightFileEnd: { line: $f.line, offset: 1 }
    }
  }')"
  curl -sSf "${auth[@]}" -X POST -d "$body" "$api?api-version=7.1" >/dev/null
  posted=$((posted + 1))
done < <(jq -c '.[]' "$findings")

echo "ado-post-findings: posted $posted new thread(s)"
