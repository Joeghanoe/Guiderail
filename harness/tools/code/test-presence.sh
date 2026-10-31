#!/usr/bin/env bash
# T.1: new behaviour ships with a test. Fails when C# source changed and no test file did.
# Changed = working tree and untracked files, plus commits since the merge base with origin/main when it exists.
# A change with no behaviour (rename, comment, formatting) names the skip: TEST_PRESENCE_SKIP="<reason>".
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# A repo with no commit yet has no HEAD to diff against: compare with the empty tree, so the first run does not fail with
# "bad revision HEAD" and every file counts as changed.
head="HEAD"
git rev-parse --verify --quiet HEAD >/dev/null || head="$(git hash-object -t tree /dev/null)"

changed="$({
  git diff --name-only "$head" --
  git ls-files --others --exclude-standard
  base="$(git merge-base origin/main HEAD 2>/dev/null || true)"
  [[ -n "$base" ]] && git diff --name-only "$base" HEAD -- || true
} | sort -u)"

is_test='(^|/)([^/]*\.)?[Tt]ests?(/|\.cs$)|[Tt]ests?\.cs$|(^|/)[^/]*\.[Tt]ests?/'
code="$(grep -E '\.cs$' <<<"$changed" | grep -vE '(^|/)(bin|obj|\.harness)/' | grep -vE "$is_test" || true)"
tests="$(grep -E '\.cs$' <<<"$changed" | grep -E "$is_test" || true)"

[[ -z "$code" || -n "$tests" ]] && exit 0
if [[ -n "${TEST_PRESENCE_SKIP:-}" ]]; then
  echo "test-presence: skipped (T.1): $TEST_PRESENCE_SKIP" >&2
  exit 0
fi
echo "test-presence: C# source changed but no test file did (T.1). Add a test that calls the new behaviour, beside the code if" >&2
echo "no test project is in reach. A change with no behaviour: set TEST_PRESENCE_SKIP=\"<reason>\"." >&2
echo "changed source: $(tr '\n' ' ' <<<"$code")" >&2
exit 1
