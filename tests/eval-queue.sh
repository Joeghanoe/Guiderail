echo "== eval-queue (stub copilot, no tokens)"
# Sourced by tests/run.sh: uses its expect helper and $here, $h, $tmp, $pass, $fail. The copilot CLI is a stub on
# PATH whose mode is a file, so each case can make it succeed, run out of quota, lose its login, or break.
eq="$h/tools/review/eval-queue.py"
qd="$tmp/eval-queue"
qbin="$qd/bin"
mkdir -p "$qbin"
: >"$qd/calls"
cat >"$qbin/copilot" <<STUB
#!/usr/bin/env bash
if [[ "\$1" == "--version" ]]; then echo "copilot 0.0.test"; exit 0; fi
echo x >>"$qd/calls"
case "\$(cat "$qd/mode")" in
  ok) echo '[]' ;;
  quota) echo "Error: 429 rate limit exceeded for premium requests" >&2; exit 1 ;;
  login) echo "Error: not logged in. Run copilot login" >&2; exit 1 ;;
  boom) echo "something unexpected broke" >&2; exit 1 ;;
esac
STUB
chmod +x "$qbin/copilot"
shim "$qbin/copilot"

py="$(command -v python3)"
mode() { echo "$1" >"$qd/mode"; }
calls() { wc -l <"$qd/calls" | tr -d ' '; }
# q <state dir> <queue args...>: the real copilot engine, with the stub first on PATH
q() { local sd="$1"; shift; PATH="$qbin:$PATH" "$py" -I "$eq" "$@" --state-dir "$sd" --results-file "$sd/results.jsonl" --engine copilot; }
sheet() { cat "$1"/copilot-default-*/checklist.md; }
has() { # has <description> <extended pattern>: the last expect's output matches
  if grep -Eq -- "$2" "$tmp/out"; then pass=$((pass + 1)); else fail=$((fail + 1)); echo "FAIL: $1"; sed 's/^/    /' "$tmp/out"; fi
}
sheet_has() { # sheet_has <state dir> <description> <extended pattern>
  if sheet "$1" | grep -Eq -- "$3"; then pass=$((pass + 1)); else fail=$((fail + 1)); echo "FAIL: $2"; sheet "$1" | sed 's/^/    /'; fi
}

G=case-c-002-log-identifiers-not-personal-data-good
B=case-c-002-log-identifiers-not-personal-data-bad
G2=case-c-003-storage-with-managed-identity-good
ONLY=(--only "$G" --only "$B" --only "$G2")

# Status costs nothing and writes nothing.
expect 0 "status lists the scenarios as unchecked" q "$qd/s0" status
has "status shows nothing checked" 'Checked off 0 of [0-9]+ scenarios'
expect 1 "status wrote no checklist" test -d "$qd/s0"
expect 0 "status ran no review" test "$(calls)" = 0

# A normal pass: results get checked off. The stub says '[]', so a good example passes and a bad one is missed.
mode ok
expect 1 "a finished run with a failing scenario fails the gate" q "$qd/s1" run "${ONLY[@]}"
has "the gate line is eval.py's own" '[0-9]+/3 passed, critical failures: none, gate: fail'
sheet_has "$qd/s1" "a good example the reviewer left alone is checked off" "^- \[x\] $G( |$)"
sheet_has "$qd/s1" "a bad example the reviewer missed is a real failure, marked" "^- \[!\] $B - FAIL: missed"
sheet_has "$qd/s1" "the third scenario is checked off too" "^- \[x\] $G2( |$)"
expect 0 "three scenarios, three reviews" test "$(calls)" = 3

# Resume: everything has a result, so nothing runs again.
expect 1 "running again finds nothing to do" q "$qd/s1" run "${ONLY[@]}"
has "it says the work is already done" '3 of 3 scenarios already have a result; 0 to run'
expect 0 "and spent no further reviews" test "$(calls)" = 3
expect 1 "--retry-failed runs only the failed one" q "$qd/s1" run "${ONLY[@]}" --retry-failed
expect 0 "that was one more review" test "$(calls)" = 4

# Running out of quota: stop at once and check nothing off. This is the point of the tool.
: >"$qd/calls"
mode quota
expect 3 "a quota error stops the run" q "$qd/s2" run "${ONLY[@]}"
has "it names the budget" 'model budget or quota'
has "it says how to resume" 'Resume with the same command'
expect 0 "it stopped at the first scenario, not the third" test "$(calls)" = 1
sheet_has "$qd/s2" "the scenario that hit the quota is marked could-not-run, not failed" '^- \[\?\] .* - ERROR:'
expect 1 "nothing was recorded as a pass" bash -c "grep -q '^- \[x\]' $qd/s2/copilot-default-*/checklist.md"
expect 1 "nothing was recorded as a fail" bash -c "grep -q '^- \[!\]' $qd/s2/copilot-default-*/checklist.md"
# ...and a later run, with budget again, finishes it and keeps the earlier work.
mode ok
: >"$qd/calls"
expect 1 "resuming after the quota resets completes the run" q "$qd/s2" run "${ONLY[@]}"
expect 0 "it ran each scenario once" test "$(calls)" = 3
expect 1 "no scenario is left could-not-run" bash -c "grep -q '^- \[?\]' $qd/s2/copilot-default-*/checklist.md"

# Other ways a run can stop.
: >"$qd/calls"
mode login
expect 3 "a login error stops the run" q "$qd/s3" run "${ONLY[@]}"
has "it tells the user to log in themselves" 'Log in to copilot yourself'
expect 0 "after one review" test "$(calls)" = 1

mode boom
: >"$qd/calls"
expect 3 "an unexplained error before anything has worked stops at once" q "$qd/s4" run "${ONLY[@]}"
has "it blames the setup, not the reviewer" 'Nothing has run successfully yet'
expect 0 "after one review" test "$(calls)" = 1
mode ok
expect 3 "--limit stops after the stated number of scenarios" q "$qd/s5" run "${ONLY[@]}" --limit 1
has "it says why it stopped" 'Stopped after 1 scenario'
expect 0 "exactly one scenario has a result" test "$(sheet "$qd/s5" | grep -c '^- \[[x!]\]')" = 1
mode boom
: >"$qd/calls"
expect 3 "once something has worked, errors in a row stop at --max-errors" q "$qd/s5" run "${ONLY[@]}" --max-errors 2
has "it counts them" '2 errors in a row'
expect 0 "two more reviews, no more" test "$(calls)" = 2

# A different reviewer is a different checklist.
mode ok
expect 0 "status for another model starts its own checklist" q "$qd/s1" status --model other-model
has "it shows nothing checked" 'Checked off 0 of'
bundle2="$tmp/eval-queue-bundle"
cp -R "$h" "$bundle2"
echo "A line that changes what the reviewer reads." >>"$bundle2/rules/code/code-1-remove-what-is-not-used.md"
expect 0 "status for a changed bundle starts a fresh checklist" q "$qd/s1" status --bundle "$bundle2"
has "it shows nothing checked" 'Checked off 0 of'
has "it keeps and mentions the earlier one" 'Older checklists for earlier states of the bundle are kept'

# History is evidence for a complete run only.
history_before="$(cksum <"$h/tools/review/history.jsonl")"
expect 1 "a partial run with --append-history still runs" q "$qd/s1" run "${ONLY[@]}" --append-history
expect 0 "but writes nothing to history.jsonl" test "$(cksum <"$h/tools/review/history.jsonl")" = "$history_before"

# Usage and setup errors.
expect 2 "an unknown scenario is a usage error" q "$qd/s6" run --only no-such-scenario
has "it lists the known ones" 'known: case-c-'
expect 2 "a missing engine CLI is reported before any work" bash -c "PATH=/usr/bin:/bin '$py' -I '$eq' run --engine copilot --state-dir '$qd/s7' --only '$G'"
expect 0 "reset removes a checklist" q "$qd/s1" reset
expect 1 "and it is gone" bash -c "test -e $qd/s1/copilot-default-*/checklist.md"

# Results are shared through a committed file: a fresh state dir (another machine) resumes from it.
expect 0 "passes and fails are recorded in the results file" test "$(grep -c . "$qd/s1/results.jsonl")" -ge 3
expect 1 "could-not-run scenarios are never recorded" grep -q '"status": "error"' "$qd/s2/results.jsonl"
mode ok
: >"$qd/calls"
mkdir -p "$qd/s8" && cp "$qd/s1/results.jsonl" "$qd/s8/results.jsonl"
expect 1 "a fresh state dir resumes from the results file" q "$qd/s8" run "${ONLY[@]}"
has "it finds the results already there" '[0-9]+ of 3 scenarios already have a result'
expect 0 "and ran no new review for them" test "$(calls)" = 0
