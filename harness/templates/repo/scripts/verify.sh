#!/usr/bin/env bash
# One verify command for local runs, the agent's Stop hook and CI (rule T.1).
# --fast (the Stop hook): incremental build and unit tests in seconds. CI never passes --fast.
# Example for a .NET solution; replace the steps with this repo's own toolchain.
set -euo pipefail
cd "$(dirname "$0")/.."

sln="${SOLUTION:-}"
for candidate in ./*.slnx ./*.sln; do
  [[ -z "$sln" && -f "$candidate" ]] && sln="$candidate"
done
[[ -n "$sln" ]] || { echo "verify: no solution found; set SOLUTION" >&2; exit 1; }

if [[ "${1:-}" == "--fast" ]]; then
  # Stop hook: seconds, not minutes. Incremental build and unit tests only.
  dotnet build "$sln" -c Release -warnaserror --nologo -v quiet
  dotnet test "$sln" --no-build -c Release --nologo -v quiet --filter "Category!=Integration"
  exit 0
fi

dotnet restore "$sln"
dotnet format "$sln" --verify-no-changes
dotnet build "$sln" --no-restore -c Release -warnaserror
dotnet test "$sln" --no-build -c Release
