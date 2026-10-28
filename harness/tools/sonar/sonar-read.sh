#!/usr/bin/env bash
# Read-only access to SonarCloud for agents (rule SEC.2: the token never leaves the environment).
#
# Tool contract (Vegviser AI Tool Boundary)
#   Classification:  Read. GET only, fixed host, allowlisted endpoints.
#   Owner:           team:teamvalue-aicoe. Version: the harness commit in .harness/VERSION.
#   Caller identity: SONAR_TOKEN, exported by the user. The agent never creates or rotates tokens.
#   Inputs:          <endpoint> [key=value ...]; values are URL-encoded here.
#   Results:         the JSON body on stdout; exit 3 with a reason when refused; exit 4 on HTTP >= 400.
#   Side effects:    none intended. A Sonar user token cannot be scoped read-only, so layer 1 is a
#                    dedicated reader account, set up by a human.
#   Review trigger:  a new endpoint, or any endpoint that returns user or token data.
#
# Usage:   sonar-read.sh issues/search componentKeys=teamvalue_X resolved=false impactSoftwareQualities=RELIABILITY,SECURITY ps=500
#          (not types=BUG: Reliability findings can be filed as code smells and a types filter drops them)
# Example: sonar-read.sh qualitygates/project_status projectKey=teamvalue_X
set -euo pipefail

refuse() {
  echo "sonar-read: refused: $1" >&2
  exit 3
}

[[ $# -ge 1 ]] || refuse "no endpoint. Usage: sonar-read.sh <endpoint> [key=value ...]"
endpoint="$1"
shift

case "$endpoint" in
  issues/search | hotspots/search | hotspots/show | qualitygates/project_status | measures/component) ;;
  *) refuse "'$endpoint' is not allowlisted (issues/search, hotspots/search, hotspots/show, qualitygates/project_status, measures/component)." ;;
esac

# The token comes from the shell, or from the user's env file (see .harness/.env.example). The file is parsed,
# not sourced, and only the two keys below are taken.
env_file="${HARNESS_ENV_FILE:-$HOME/.config/harness/.env}"
if [[ -f "$env_file" ]]; then
  for key in SONAR_TOKEN SONAR_ORGANIZATION; do
    if [[ -z "${!key:-}" ]]; then
      value="$(sed -n "s/^${key}=//p" "$env_file" | tail -n 1)"
      value="${value%\"}"
      value="${value#\"}"
      [[ -z "$value" ]] || export "$key=$value"
    fi
  done
fi
[[ -n "${SONAR_TOKEN:-}" ]] || refuse "SONAR_TOKEN is missing. The user sets it in $env_file (see .harness/.env.example for how to create one); the agent does not."

args=(--get --data-urlencode "organization=${SONAR_ORGANIZATION:-teamvalue}")
for kv in "$@"; do
  [[ "$kv" == *=* ]] || refuse "'$kv' is not key=value."
  [[ "${kv%%=*}" == "organization" ]] && continue
  args+=(--data-urlencode "$kv")
done

body="$(mktemp)"
trap 'rm -f "$body"' EXIT
# The token goes in through a curl config on stdin, so it never appears in the process list.
status="$(printf 'user = "%s:"\n' "$SONAR_TOKEN" | curl -sS -K - "${args[@]}" -o "$body" -w '%{http_code}' "https://sonarcloud.io/api/$endpoint")"
cat "$body"
if ((status >= 400)); then
  echo "sonar-read: HTTP $status" >&2
  ((status != 401)) || echo "sonar-read: the token is expired or wrong. The user renews it (see .harness/.env.example)." >&2
  exit 4
fi
