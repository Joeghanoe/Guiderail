#!/usr/bin/env bash
# Deliver successful, content-deduplicated lookups before edits. Lookup errors block the edit.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -I "$here/../tools/harness/context.py"
