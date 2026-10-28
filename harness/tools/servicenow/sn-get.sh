#!/usr/bin/env bash
# Read-only access to the ServiceNow Table API for agents (rules CLD.1 and SEC.2).
#
# Tool contract (Vegviser AI Tool Boundary)
#   Classification:  Read. GET only, fixed host pattern, allowlisted configuration tables.
#   Owner:           team:teamvalue-aicoe. Version: the harness commit in .harness/VERSION.
#   Caller identity: SN_INSTANCE, SN_USER, SN_PASSWORD, set by the user in the harness env file. Use a
#                    sub-prod instance and a service account with read ACLs only. The agent never creates it.
#   Inputs:          <table> ["<encoded query>"] ["field,field"]
#   Results:         a JSON array of all records on stdout, or, with SN_SNAPSHOT_DIR set, written to
#                    $SN_SNAPSHOT_DIR/<table>/<slug>.json with the path on stdout.
#                    Exit 3: refused, or HTTP 403 (no read access: report the gap, do not work around it).
#                    Exit 4: HTTP >= 400 otherwise.
#   Side effects:    none intended; the allowlist holds configuration and metadata tables only, never
#                    case, incident, user or other business data (SEC.2).
#   Review trigger:  a new table on the allowlist, or any table that holds personal or case data.
#
# Usage:   sn-get.sh sys_script "collection=incident^active=true" "sys_id,name,when,order,script"
#          sn-get.sh sys_choice "name=incident^element=category" "value,label"
# A table that is not on the allowlist is a question for the user.
set -euo pipefail

ALLOWED_TABLES=(
  sys_update_set             # local update sets: name, state, application, parent
  sys_update_xml             # customer updates per update set, including payload
  sys_remote_update_set      # loaded remote update sets and their preview state
  sys_update_preview_problem # preview problems per remote update set
  sys_update_version         # version history per configuration record
  sys_update_set_source      # update set sources (origin instances)
  sys_scope                  # application scopes
  sys_app                    # custom applications
  sys_metadata               # all configuration records (sys_class_name, scope)
  sys_db_object              # table definitions and hierarchy (super_class)
  sys_dictionary             # field definitions: type, reference, mandatory, default
  sys_transform_map          # transform maps: source and target table, onBefore script
  sys_transform_entry        # field maps: source to target, coalesce, source script
  sys_transform_script       # transform event scripts (onStart, onBefore, onAfter, ...)
  sys_data_source            # data sources: import set table, type, format
  scheduled_import_set       # scheduled imports: data source, schedule, pre and post script
  sys_script                 # business rules: table, when, order, condition, script
  sys_script_include         # script includes: reusable server-side logic
  sysauto_script             # scheduled script jobs: script and schedule
  sys_hub_flow               # Flow Designer flows: metadata (name, status, scope)
  sys_choice                 # choice values per table and field
  sys_ws_definition          # scripted REST APIs: name, namespace, base path
  sys_ws_operation           # scripted REST API resources: method, path, script
  sysevent_in_email_action   # inbound email actions: condition, script
  sys_ui_policy              # UI policies: table, conditions
  sys_client_script          # client scripts: table, type, script
)

sn_is_allowed() {
  local t
  for t in "${ALLOWED_TABLES[@]}"; do
    [[ "$t" == "$1" ]] && return 0
  done
  return 1
}

sn_refuse() {
  echo "sn-get: refused: $1" >&2
  exit 3
}

# The credentials come from the shell, or from the user's harness env file (see harness/.env.example). The
# file is parsed, not sourced, and only the three keys below are taken.
sn_load_env() {
  local env_file="${HARNESS_ENV_FILE:-$HOME/.config/harness/.env}" key value
  if [[ -f "$env_file" ]]; then
    for key in SN_INSTANCE SN_USER SN_PASSWORD; do
      if [[ -z "${!key:-}" ]]; then
        value="$(sed -n "s/^${key}=//p" "$env_file" | tail -n 1)"
        value="${value%\"}"
        value="${value#\"}"
        [[ -z "$value" ]] || export "$key=$value"
      fi
    done
  fi
  for key in SN_INSTANCE SN_USER SN_PASSWORD; do
    [[ -n "${!key:-}" ]] || sn_refuse "$key is missing. The user sets it in $env_file (see harness/.env.example); the agent does not."
  done
  [[ "$SN_INSTANCE" =~ ^[a-z0-9-]+\.service-now\.com$ ]] || sn_refuse "SN_INSTANCE must be <name>.service-now.com, without https:// or a path."
}

# sn_request <table> <outfile> [curl args]: one GET; the body goes to <outfile>, the HTTP status to stdout.
# The credentials go in through a curl config on stdin, so they never appear in the process list.
sn_request() {
  local table="$1" out="$2"
  shift 2
  sn_is_allowed "$table" || sn_refuse "table '$table' is not on the allowlist. Ask the user."
  printf 'user = "%s:%s"\n' "$SN_USER" "$SN_PASSWORD" |
    curl --silent --show-error --get --config - --header "Accept: application/json" \
      --output "$out" --write-out '%{http_code}' "$@" "https://${SN_INSTANCE}/api/now/table/${table}"
}

# Sourced by sn-access-check.sh: only the definitions above.
[[ "${BASH_SOURCE[0]}" != "$0" ]] && return 0

[[ $# -ge 1 ]] || sn_refuse 'no table. Usage: sn-get.sh <table> ["<encoded query>"] ["field,field"]'
table="$1"
query="${2:-}"
fields="${3:-}"
sn_is_allowed "$table" || sn_refuse "table '$table' is not on the allowlist. Ask the user."
sn_load_env

page_size="${SN_PAGE_SIZE:-500}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
echo '[]' >"$work/all"

offset=0
while :; do
  params=(
    --data-urlencode "sysparm_limit=$page_size"
    --data-urlencode "sysparm_offset=$offset"
    --data-urlencode "sysparm_exclude_reference_link=true"
  )
  [[ -z "$query" ]] || params+=(--data-urlencode "sysparm_query=$query")
  [[ -z "$fields" ]] || params+=(--data-urlencode "sysparm_fields=$fields")

  status="$(sn_request "$table" "$work/page" "${params[@]}")" || {
    echo "sn-get: request to $table failed (curl)." >&2
    exit 4
  }
  case "$status" in
    200) ;;
    403)
      echo "sn-get: no read access on $table (HTTP 403). Report the gap to the user; do not work around it." >&2
      exit 3
      ;;
    *)
      echo "sn-get: HTTP $status on $table" >&2
      exit 4
      ;;
  esac

  count="$(jq '.result | length' "$work/page")"
  jq -s '.[0] + .[1].result' "$work/all" "$work/page" >"$work/merged"
  mv "$work/merged" "$work/all"
  ((count >= page_size)) || break
  offset=$((offset + page_size))
done

if [[ -n "${SN_SNAPSHOT_DIR:-}" ]]; then
  slug="$(printf '%s|%s' "$query" "$fields" | shasum | cut -c1-12)"
  mkdir -p "$SN_SNAPSHOT_DIR/$table"
  jq 'sort_by(.sys_id)' "$work/all" >"$SN_SNAPSHOT_DIR/$table/$slug.json"
  printf '%s\n' "$SN_SNAPSHOT_DIR/$table/$slug.json"
else
  jq '.' "$work/all"
fi
