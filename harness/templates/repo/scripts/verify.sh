#!/usr/bin/env bash
# One verify command for local runs, the agent's Stop hook and CI (rule T.1).
# --fast (the Stop hook): incremental build and unit tests in seconds. CI never passes --fast.
# --design: only the design gate (design, ADRs, AGENTS.md); run it before the first file under src/.
# Example for a .NET solution; replace the steps with this repo's own toolchain.
set -euo pipefail
cd "$(dirname "$0")/.."

# Design gate (DEL.4, CODE.8, OBS.3, T.3): static, takes milliseconds, runs in both modes.
DESIGN_PROFILE=generic # generic | service | web-app; greenfield-init.sh writes this
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

# CODE.5 runs independently of guidance selection. CI may run it once as a separate required step.
if [[ "${HARNESS_CODE5_EXTERNAL:-0}" == "1" ]]; then
  echo "verify: CODE.5 delegated to the independent CI step"
else
  [[ -n "$harness" && -f "$harness/tools/verification/verify.py" ]] || {
    echo "verify: CODE.5 runner unavailable; verification incomplete" >&2; exit 2;
  }
  evidence="${HARNESS_EVIDENCE_DIR:-$(mktemp -d)}/code-types"
  code5_args=(--repo "$PWD" --out "$evidence")
  [[ -z "${HARNESS_BASE_REF:-}" ]] || code5_args+=(--baseline "$HARNESS_BASE_REF")
  if [[ -n "${CODE5_SYMBOLS:-}" ]]; then
    IFS=';' read -r -a configurations <<<"$CODE5_SYMBOLS"
    for configuration in "${configurations[@]}"; do code5_args+=(--symbols "$configuration"); done
  fi
  python3 -I "$harness/tools/verification/verify.py" code-types "${code5_args[@]}"
fi

dotnet restore "$sln"
dotnet format "$sln" --verify-no-changes
dotnet build "$sln" --no-restore -c Release -warnaserror
dotnet test "$sln" --no-build -c Release

# Other toolchains in this repo (a frontend, an extension): list their folders and each is installed from its lockfile, then
# format-checked, built and tested with its own scripts (T.1). A step the project does not define is named, never skipped silently.
NODE_PROJECTS=() # for example (src/frontend src/directus/extensions/macro-hook)
for project in ${NODE_PROJECTS[@]+"${NODE_PROJECTS[@]}"}; do
  bash "$harness/tools/code/node-verify.sh" "$project"
done

# Layer 1 integration against containers (T.3). Skipped, and said so, when Docker is not available: CI runs it.
if [[ -f scripts/integration.sh ]]; then
  if docker info >/dev/null 2>&1; then
    bash scripts/integration.sh
  else
    echo "verify: integration tests SKIPPED (Docker not available); CI runs them" >&2
  fi
fi
