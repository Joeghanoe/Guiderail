#!/usr/bin/env bash
# The agent's quick local verify for one project (rule T.1). It lives in ~/.golden-path-harness/projects/<repo-id>/, not in the
# repo: CI is the authority and runs the full gate. A check CI misses is added here; a critical one is proposed to the repo's
# CI as a diff for a human (CLD.2), so the repo gets neither a second pipeline nor a copy of this file.
# --fast (the Stop hook): the static gates, then an incremental build and unit tests in seconds.
# --design: only the design gate (design, ADRs, AGENTS.md); run it before the first file under src/.
# Every check runs even when an earlier one failed, so a failing design gate cannot hide a CODE.5 violation; the exit code is
# non-zero when any of them failed. Example for a .NET solution; replace the steps with this repo's own toolchain.
set -uo pipefail
cd "${HARNESS_REPO_ROOT:-$(git rev-parse --show-toplevel)}"
failed=0
mode="${1:-}"

# Design gate (DEL.4, CODE.8, OBS.3, T.3): static, takes milliseconds, runs in every mode.
DESIGN_PROFILE=generic # generic | service | web-app; project-verify.sh init writes this
harness=""
for candidate in ./.harness "$HOME/.golden-path-harness/harness"; do
  [[ -z "$harness" && -f "$candidate/tools/greenfield/design-check.py" ]] && harness="$candidate"
done
if [[ -n "$harness" ]]; then
  design_only=()
  [[ "$mode" == "--design" ]] && design_only=(--design-only)
  python3 -I "$harness/tools/greenfield/design-check.py" . --profile "$DESIGN_PROFILE" ${design_only[@]+"${design_only[@]}"} || failed=1
else
  echo "verify: harness not found; skipping the design gate" >&2
fi

[[ "$mode" == "--design" ]] && exit "$failed"

# T.1: new behaviour ships with a test. Static, takes milliseconds, runs in every mode.
if [[ -n "$harness" && -f "$harness/tools/code/test-presence.sh" ]]; then
  bash "$harness/tools/code/test-presence.sh" || failed=1
fi

# Rules for the files this change touches, by path (CODE.* only apply to code, so they are missing until code exists).
if [[ -n "$harness" ]]; then
  echo "verify: rules that apply to the changed files:" >&2
  python3 -I "$harness/tools/harness/bundle.py" select --brief --changed 2>/dev/null | cut -d: -f1 | tr '\n' ' ' >&2 || true
  echo >&2
fi

# CODE.5 runs independently of guidance selection and of the design gate, in every mode. CI may run it once as a separate required step.
if [[ "${HARNESS_CODE5_EXTERNAL:-0}" == "1" ]]; then
  echo "verify: CODE.5 delegated to the independent CI step"
elif [[ -z "$harness" || ! -f "$harness/tools/verification/verify.py" ]]; then
  echo "verify: CODE.5 runner unavailable; verification incomplete" >&2
  failed=1
else
  evidence="${HARNESS_EVIDENCE_DIR:-$(mktemp -d)}/code-types"
  code5_args=(--repo "$PWD" --out "$evidence")
  [[ -z "${HARNESS_BASE_REF:-}" ]] || code5_args+=(--baseline "$HARNESS_BASE_REF")
  if [[ -n "${CODE5_SYMBOLS:-}" ]]; then
    IFS=';' read -r -a configurations <<<"$CODE5_SYMBOLS"
    for configuration in "${configurations[@]}"; do code5_args+=(--symbols "$configuration"); done
  fi
  python3 -I "$harness/tools/verification/verify.py" code-types "${code5_args[@]}" || failed=1
fi

sln="${SOLUTION:-}"
for candidate in ./*.slnx ./*.sln; do
  [[ -z "$sln" && -f "$candidate" ]] && sln="$candidate"
done
if [[ -z "$sln" ]]; then
  echo "verify: no solution found; set SOLUTION" >&2
  exit 1
fi

if [[ "$mode" == "--fast" ]]; then
  # Stop hook: seconds, not minutes. Incremental build and unit tests only.
  dotnet build "$sln" -c Release -warnaserror --nologo -v quiet &&
    dotnet test "$sln" --no-build -c Release --nologo -v quiet --filter "Category!=Integration" || failed=1
  exit "$failed"
fi

dotnet restore "$sln" &&
  dotnet format "$sln" --verify-no-changes &&
  dotnet build "$sln" --no-restore -c Release -warnaserror &&
  dotnet test "$sln" --no-build -c Release || failed=1

# Other toolchains in this repo (a frontend, an extension): list their folders and each is installed from its lockfile, then
# format-checked, built and tested with its own scripts (T.1). A step the project does not define is named, never skipped silently.
NODE_PROJECTS=() # for example (src/frontend src/directus/extensions/macro-hook)
for project in ${NODE_PROJECTS[@]+"${NODE_PROJECTS[@]}"}; do
  bash "$harness/tools/code/node-verify.sh" "$project" || failed=1
done

# Layer 1 integration against containers (T.3). Skipped, and said so, when Docker is not available: CI runs it.
if [[ -f scripts/integration.sh ]]; then
  if docker info >/dev/null 2>&1; then
    bash scripts/integration.sh || failed=1
  else
    echo "verify: integration tests SKIPPED (Docker not available); CI runs them" >&2
  fi
fi

exit "$failed"
