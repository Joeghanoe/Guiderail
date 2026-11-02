#!/usr/bin/env bash
# Shared by the read-only Azure DevOps run tools (ado-run-failure.sh, ado-run-watch.sh). Sourced, not run.
# Needs `tool` set by the caller for messages. GET only, fixed host; the token is requested for the Azure
# DevOps resource only, goes to curl on stdin and is never printed (SEC.2). The agent never logs in (CLD.1).

ado_refuse() {
  echo "$tool: refused: $1" >&2
  exit 3
}

# ado_init <organization-url> <project>: validates the inputs and sets ado_org and ado_project (URL-encoded).
ado_init() {
  ado_org="${1%/}"
  [[ "$ado_org" =~ ^https://dev\.azure\.com/[A-Za-z0-9._-]+$ ]] || ado_refuse "organization must be https://dev.azure.com/<name>."
  ado_project="$(jq -rn --arg p "$2" '$p | @uri')"
  if [[ -n "${HARNESS_AZURE_CONFIG_DIR:-}" ]]; then
    export AZURE_CONFIG_DIR="$HARNESS_AZURE_CONFIG_DIR"
  fi
  ado_token
}

# ado_token: fetches a fresh token; a long watch calls it again, because tokens last about an hour.
# 499b84ac-... is the fixed Azure DevOps resource id.
ado_token() {
  ado_bearer="$(az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv 2>/dev/null)" ||
    ado_refuse "not logged in to az. The user runs 'az login'; the agent does not."
}

# ado_get <url>: body on stdout; exit 4 on HTTP >= 400.
ado_get() {
  local body status
  body="$(mktemp)"
  status="$(printf 'header = "Authorization: Bearer %s"\n' "$ado_bearer" | curl -sS -K - -o "$body" -w '%{http_code}' "$1")"
  cat "$body"
  rm -f "$body"
  if ((status >= 400)); then
    echo "$tool: HTTP $status from $1" >&2
    exit 4
  fi
}
