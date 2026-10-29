echo "== compare-ui"
# Sourced by tests/run.sh: uses its expect helper and $here, $h, $tmp. Fixtures are synthetic reports in screenshot.mjs's shape.
cui="$h/tools/frontend/compare-ui.mjs"
cuid="$tmp/compare-ui"
mkdir -p "$cuid"

# mkrun <dir> <findings at 320x640 as JSON> [findings at 1280x800 as JSON] [axe status]
mkrun() {
  mkdir -p "$1"
  jq -n --argjson narrow "$2" --argjson wide "${3:-[]}" --arg axe "${4:-run}" \
    '{axe: $axe, shots: [
       {file: "page-1-320x640.png", url: "http://localhost:5173/orders", viewport: "320x640", scheme: "light", findings: $narrow},
       {file: "page-1-1280x800.png", url: "http://localhost:5173/orders", viewport: "1280x800", scheme: "light", findings: $wide}]}' >"$1/report.json"
}
cui_says() { # cui_says <grep pattern> <compare-ui args...>: the combined output matches the pattern, whatever the exit code
  local pattern="$1" output
  shift
  output="$(node "$cui" "$@" 2>&1)"
  grep -q -- "$pattern" <<<"$output"
}
cui_json() { # cui_json <jq expression> <compare-ui args...>
  local expression="$1" output
  shift
  output="$(node "$cui" "$@" --json 2>&1)"
  jq -e "$expression" <<<"$output" >/dev/null
}

contrast='{"check":"contrast","wcag":"1.4.3 Contrast (Minimum)","detail":"p.hint \"Synthetic\" is 2.10:1, needs 4.5:1"}'
tiny='{"check":"target-size-min","wcag":"2.5.8 Target Size (Minimum)","detail":"button.x \"Go\" is 18x18px, below 24x24"}'
axelink7='{"check":"axe:link-name","wcag":"wcag2a wcag412","detail":"Links must have discernible text (7 nodes, first: a.card)"}'
axelink3='{"check":"axe:link-name","wcag":"wcag2a wcag412","detail":"Links must have discernible text (3 nodes, first: a.card)"}'
axelink9='{"check":"axe:link-name","wcag":"wcag2a wcag412","detail":"Links must have discernible text (9 nodes, first: a.card)"}'
scroll='{"check":"horizontal-scroll","wcag":"1.4.10 Reflow","detail":"page is 412px wide in a 320px viewport"}'

mkrun "$cuid/base" "[$contrast, $axelink7, $scroll]" "[$contrast]"
mkrun "$cuid/same" "[$contrast, $axelink7, $scroll]" "[$contrast]"
mkrun "$cuid/fixed" "[$contrast, $axelink7]" "[$contrast]"
mkrun "$cuid/new" "[$contrast, $axelink7, $scroll, $tiny]" "[$contrast]"
mkrun "$cuid/swap" "[$contrast, $axelink7, $tiny]" "[$contrast]"
mkrun "$cuid/reduced" "[$contrast, $axelink3, $scroll]" "[$contrast]"
mkrun "$cuid/increased" "[$contrast, $axelink9, $scroll]" "[$contrast]"
mkrun "$cuid/reordered" "[$scroll, $axelink7, $contrast]" "[$contrast]"
mkrun "$cuid/noaxe" "[$contrast, $scroll]" "[$contrast]" "not run: axe-core is not installed in this repo"
mkdir -p "$cuid/malformed" "$cuid/notreport" "$cuid/emptydir"
echo '{"axe": "run", "shots": [' >"$cuid/malformed/report.json"
echo '{"axe": "run", "shots": [{"url": "http://localhost:5173/", "viewport": "320x640", "scheme": "light"}]}' >"$cuid/notreport/report.json"
jq '.shots |= map(select(.viewport == "320x640"))' "$cuid/base/report.json" >"$cuid/narrow-only.json"
jq '.shots[0].findings[1].detail = "Links must have discernible text (7 nodes, first: a.other)" | .shots[0].findings |= reverse' "$cuid/base/report.json" >"$cuid/detail-drift.json"

expect 0 "compare-ui: identical runs" node "$cui" --before "$cuid/base" --after "$cuid/same"
expect 0 "compare-ui: identical runs say so" cui_says "new 0, increased 0, reduced 0, fixed 0, unchanged 4" --before "$cuid/base" --after "$cuid/same"
expect 0 "compare-ui: a report.json path works as well as a run folder" node "$cui" --before "$cuid/base/report.json" --after "$cuid/same/report.json"
expect 0 "compare-ui: finding order and detail text do not matter" node "$cui" --before "$cuid/base" --after "$cuid/reordered"
expect 0 "compare-ui: a changed selector in detail is not a new finding" node "$cui" --before "$cuid/base/report.json" --after "$cuid/detail-drift.json"
expect 0 "compare-ui: a fixed finding exits 0" node "$cui" --before "$cuid/base" --after "$cuid/fixed"
expect 0 "compare-ui: the fixed finding is named" cui_says "FIXED" --before "$cuid/base" --after "$cuid/fixed"
expect 0 "compare-ui: fixed is counted once, in the 320 row" cui_json '.summary.fixed == 1 and (.findings[] | select(.status == "fixed") | .check == "horizontal-scroll" and .viewport == "320x640")' --before "$cuid/base" --after "$cuid/fixed"
expect 2 "compare-ui: a new finding exits 2" node "$cui" --before "$cuid/base" --after "$cuid/new"
expect 0 "compare-ui: the new finding is flagged as a regression" cui_says "NEW (absent in the baseline" --before "$cuid/base" --after "$cuid/new"
expect 0 "compare-ui: new is attributed to the 320 viewport only" cui_json '.summary.new == 1 and ([.perViewport[] | select(.new > 0) | .viewport] == ["320x640"])' --before "$cuid/base" --after "$cuid/new"
expect 2 "compare-ui: trading one violation for another still exits 2" node "$cui" --before "$cuid/base" --after "$cuid/swap"
expect 0 "compare-ui: a swap shows one fixed and one new" cui_json '.summary.fixed == 1 and .summary.new == 1' --before "$cuid/base" --after "$cuid/swap"
expect 0 "compare-ui: a reduced node count is reduced, not fixed" cui_json '.summary.reduced == 1 and .summary.fixed == 0 and .summary.new == 0 and (.findings[] | select(.status == "reduced") | .before == 7 and .after == 3 and .countBasis == "nodes")' --before "$cuid/base" --after "$cuid/reduced"
expect 0 "compare-ui: a reduced count exits 0" node "$cui" --before "$cuid/base" --after "$cuid/reduced"
expect 0 "compare-ui: the table shows the node counts" cui_says "7 -> 3 nodes" --before "$cuid/base" --after "$cuid/reduced"
expect 0 "compare-ui: a rise in count is increased, not new" cui_json '.summary.increased == 1 and .summary.new == 0' --before "$cuid/base" --after "$cuid/increased"
expect 0 "compare-ui: presence-only comparison is stated" cui_says "compared by presence only" --before "$cuid/base" --after "$cuid/same"
expect 0 "compare-ui: --baseline-name and --after-name label the columns" cui_says "round1.*round2" --before "$cuid/base" --after "$cuid/fixed" --baseline-name round1 --after-name round2
expect 0 "compare-ui: the scope limit is printed every time" cui_says "does not score the design" --before "$cuid/base" --after "$cuid/same"
expect 0 "compare-ui: --json is one parseable object" cui_json '.summary.unchanged == 4 and (.scope | test("not evidence"))' --before "$cuid/base" --after "$cuid/same"
expect 0 "compare-ui: detail text never reaches the output" bash -c "! node '$cui' --before '$cuid/base' --after '$cuid/new' 2>&1 | grep -q 'Synthetic'"

expect 1 "compare-ui: no arguments is a usage error" node "$cui"
expect 1 "compare-ui: --after is required" node "$cui" --before "$cuid/base"
expect 1 "compare-ui: an unknown option is a usage error" node "$cui" --before "$cuid/base" --after "$cuid/same" --frobnicate
expect 1 "compare-ui: an option without a value is a usage error" node "$cui" --before "$cuid/base" --after
expect 1 "compare-ui: a missing file" node "$cui" --before "$cuid/base" --after "$cuid/does-not-exist"
expect 1 "compare-ui: a folder without report.json" node "$cui" --before "$cuid/emptydir" --after "$cuid/base"
expect 1 "compare-ui: a malformed report" node "$cui" --before "$cuid/base" --after "$cuid/malformed"
expect 0 "compare-ui: a malformed report is named" cui_says "not readable JSON" --before "$cuid/malformed" --after "$cuid/base"
expect 1 "compare-ui: a report without a findings array" node "$cui" --before "$cuid/notreport" --after "$cuid/base"
expect 1 "compare-ui: runs over different screens are refused" node "$cui" --before "$cuid/base" --after "$cuid/narrow-only.json"
expect 0 "compare-ui: ...and the refusal says why" cui_says "cover different screens" --before "$cuid/base" --after "$cuid/narrow-only.json"
expect 0 "compare-ui: --allow-partial compares the overlap" node "$cui" --before "$cuid/base" --after "$cuid/narrow-only.json" --allow-partial
expect 1 "compare-ui: axe in one run and not the other is refused" node "$cui" --before "$cuid/base" --after "$cuid/noaxe"
expect 0 "compare-ui: --allow-partial drops axe checks instead of calling them fixed" cui_json '.summary.fixed == 0 and .partial.axeExcluded == true' --before "$cuid/base" --after "$cuid/noaxe" --allow-partial
