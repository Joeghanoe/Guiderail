#!/usr/bin/env bash
# agy hook uses the same successful lookup and content cache as the Claude hook.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -I "$here/../tools/harness/context.py" --agy
