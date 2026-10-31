#!/usr/bin/env bash
# One verify command for local runs, the agent's Stop hook and CI (rule T.1).
# --fast (the Stop hook): incremental build and unit tests in seconds. CI never passes --fast.
# --design: only the design gate (design, ADRs, AGENTS.md); run it before the first file under src/.
# Example for a .NET solution; replace the steps with this repo's own toolchain.
set -euo pipefail
cd "$(dirname "$0")/.."

# Design gate (DEL.4, CODE.8, OBS.3, T.3): static, takes milliseconds, runs in both modes.
DESIGN_PROFILE=generic # generic | service; greenfield-init.sh writes this
harness=""
for candidate in ./.harness "$HOME/.golden-path-harness/harness"; do
  [[ -z "$harness" && -f "$candidate/tools/greenfield/design-check.py" ]] && harness="$candidate"
done
if [[ -n "$harness" ]]; then
  design_only=()
  [[ "${1:-}" == "--design" ]] && design_only=(--design-only)
  python3 -I "$harness/tools/greenfield/design-check.py" . --profile "$DESIGN_PROFILE" ${design_only[@]+"${design_only[@]}"}
else
  echo "verify: harness not found; skipping the design gate" >&2
fi

[[ "${1:-}" == "--design" ]] && exit 0

# T.1: new behaviour ships with a test. Static, takes milliseconds, runs in both modes.
[[ -n "$harness" && -f "$harness/tools/code/test-presence.sh" ]] && bash "$harness/tools/code/test-presence.sh"

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

# CODE.5: one type per file, from the harness checker (needs the .NET SDK; syntax only).
if [[ -n "$harness" && -f "$harness/tools/code/CheckTypes.csproj" ]]; then
  checker="$(mktemp -d)"
  trap 'rm -rf "$checker"' EXIT
  cp -R "$harness/tools/code/." "$checker/"
  rm -rf "$checker/bin" "$checker/obj"
  dotnet build "$checker/CheckTypes.csproj" -c Release -o "$checker/out" --nologo -v q >/dev/null
  sources=()
  while IFS= read -r source; do sources+=("${source#./}"); done < <(find . -name '*.cs' -not -path '*/bin/*' -not -path '*/obj/*' -not -path './.harness/*')
  [[ ${#sources[@]} -eq 0 ]] || dotnet "$checker/out/CheckTypes.dll" "${sources[@]}" >/dev/null || { echo "verify: CODE.5 findings; run the checker for the list" >&2; exit 1; }
fi

dotnet restore "$sln"
dotnet format "$sln" --verify-no-changes
dotnet build "$sln" --no-restore -c Release -warnaserror
dotnet test "$sln" --no-build -c Release
