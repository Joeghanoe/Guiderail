#!/usr/bin/env bash
# Checks per allowlisted table whether the service account can read it: one GET with limit 1, nothing stored.
# Run it at the start of a ServiceNow session; the result says which tables you can use.
#
# Usage:  sn-access-check.sh
# Output: one line per table on stdout: OK, 403, or error (HTTP code). Exit 0 when the check ran.
# A table can be OK here and still return 403 for a query: ACLs can also work per record or per field.
set -euo pipefail

# shellcheck source-path=SCRIPTDIR source=sn-get.sh
source "$(cd "$(dirname "$0")" && pwd)/sn-get.sh" # ALLOWED_TABLES, sn_load_env, sn_request
sn_load_env

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

echo "instance: $SN_INSTANCE ($(date -u +%FT%TZ))"
for table in "${ALLOWED_TABLES[@]}"; do
  status="$(sn_request "$table" "$tmp" --data-urlencode "sysparm_limit=1" --data-urlencode "sysparm_fields=sys_id")" || status="000"
  case "$status" in
    200) result="OK" ;;
    403) result="403" ;;
    *) result="error (HTTP $status)" ;;
  esac
  printf '%-28s %s\n' "$table" "$result"
done
