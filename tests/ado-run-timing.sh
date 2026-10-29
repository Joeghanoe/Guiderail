echo "== ado-run-timing"
# Sourced by tests/run.sh: uses its expect helper and $here, $h, $tmp. No network: az and curl are stubs on PATH.
# The fixture is one pipeline: Build -> {Test, Scan} -> Publish. Test (Unit, Integration) is the long branch, Scan is
# shorter and off the critical path, so the critical path is neither the sum of the stages nor the longest one.
tm="$tmp/timing"
mkdir -p "$tm" "$tmp/timing-bin"

cat >"$tmp/timing-bin/az" <<'STUB'
#!/usr/bin/env bash
printf '%s\n' "$*" >>"$STUB_DIR/az.log"
[[ "$1 $2" == "account get-access-token" ]] && { echo stub-token; exit 0; }
exit 1
STUB
cat >"$tmp/timing-bin/curl" <<'STUB'
#!/usr/bin/env bash
cat >/dev/null
printf '%s\n' "$*" >>"$STUB_DIR/curl.log"
out=; url=
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o) out="$2"; shift ;;
    -w | -K) shift ;;
    -*) ;;
    *) url="$1" ;;
  esac
  shift
done
f=
case "$url" in
  */timeline\?*) id="${url%/timeline*}"; id="${id##*/}"; f="timeline-$id.json" ;;
  */build/builds\?*) f="list.json" ;;
  */build/builds/*) id="${url##*/builds/}"; id="${id%%\?*}"; f="run-$id.json" ;;
  */build/definitions\?*) f="definitions.json" ;;
esac
if [[ -n "$f" && -f "$STUB_DIR/$f" ]]; then
  cp "$STUB_DIR/$f" "$out"
  printf 200
else
  echo '{"message":"not found"}' >"$out"
  printf 404
fi
STUB
chmod +x "$tmp/timing-bin/az" "$tmp/timing-bin/curl"

# tm_fixture <id> <run queue s> <agent queue of Integration s> <Integration execution s> <Restore s> [live]
# Writes run-<id>.json and timeline-<id>.json. Times are offsets from the moment the run was queued.
tm_fixture() {
  cat >"$tm/fixture.jq" <<'JQ'
def t0: ("2026-10-20T08:00:00Z" | fromdateiso8601);
def iso($s): if $s == null then null else (t0 + $s) | todate | sub("Z$"; ".1234567Z") end;
def fin($x): if $live then null else $x end;
def r($id; $parent; $type; $name; $s; $f): {
  id: $id, parentId: $parent, type: $type, name: $name, identifier: $name, order: 1,
  startTime: iso($s), finishTime: iso($f),
  state: (if $s == null then "pending" elif $f == null then "inProgress" else "completed" end),
  result: (if $s != null and $f != null then "succeeded" else null end)
};
$q as $S
| ($S + 170 + $rdur) as $bf
| ($bf + 2 + $iq + $idur) as $tf
| ($tf + 105) as $rf
| {
  run: {
    id: $id, buildNumber: "2026.10.\($id)",
    status: (if $live then "inProgress" else "completed" end),
    result: (if $live then null else "succeeded" end),
    queueTime: iso(0), startTime: iso($S), finishTime: iso(fin($rf)),
    definition: {id: 7, name: "Team-CI"}
  },
  timeline: { records: ([
    r("stage-build"; null; "Stage"; "Build"; $S + 5; $bf),
    r("phase-compile"; "stage-build"; "Phase"; "Compile"; $S + 5; $bf),
    r("job-compile"; "phase-compile"; "Job"; "Compile"; $S + 45; $bf),
    r("c1"; "job-compile"; "Task"; "Initialize job"; $S + 45; $S + 48),
    r("c2"; "job-compile"; "Task"; "Restore"; $S + 48; $S + 48 + $rdur),
    r("c3"; "job-compile"; "Task"; "Bash"; $S + 48 + $rdur; $S + 50 + $rdur),
    r("c4"; "job-compile"; "Task"; "Bash"; $S + 50 + $rdur; $S + 52 + $rdur),
    r("c5"; "job-compile"; "Task"; "Build"; $S + 52 + $rdur; $S + 168 + $rdur),
    r("c6"; "job-compile"; "Task"; "Finalize Job"; $S + 168 + $rdur; $bf),

    r("stage-scan"; null; "Stage"; "Scan"; $bf + 1; $bf + 401),
    r("phase-scan"; "stage-scan"; "Phase"; "Scan"; $bf + 1; $bf + 401),
    r("job-scan"; "phase-scan"; "Job"; "Scan"; $bf + 15; $bf + 401),
    r("s1"; "job-scan"; "Task"; "Scan"; $bf + 15; $bf + 400),
    r("s2"; "job-scan"; "Task"; "Finalize Job"; $bf + 400; $bf + 401),

    r("stage-test"; null; "Stage"; "Test"; $bf + 2; fin($tf)),
    r("phase-unit"; "stage-test"; "Phase"; "Unit"; $bf + 2; fin($bf + 225)),
    r("job-unit"; "phase-unit"; "Job"; "Unit"; $bf + 25; $bf + 225),
    r("u1"; "job-unit"; "Task"; "Run unit tests"; $bf + 28; $bf + 223),
    r("u2"; "job-unit"; "Task"; "Evil\u001b[31m\tname"; $bf + 223; $bf + 224),
    r("phase-int"; "stage-test"; "Phase"; "Integration"; $bf + 2; fin($tf)),
    r("job-int"; "phase-int"; "Job"; "Integration"; $bf + 2 + $iq; fin($tf)),
    r("i1"; "job-int"; "Task"; "Initialize job"; $bf + 2 + $iq; $bf + 5 + $iq),
    r("i2"; "job-int"; "Task"; "Run integration tests"; $bf + 5 + $iq; fin($tf - 2))
  ] + (if $live then [
    r("stage-publish"; null; "Stage"; "Publish"; null; null)
  ] else [
    r("i3"; "job-int"; "Task"; "Finalize Job"; $tf - 2; $tf),
    r("stage-publish"; null; "Stage"; "Publish"; $tf + 3; $tf + 103),
    r("cp1"; "stage-publish"; "Checkpoint"; "Checkpoint"; $tf + 3; $tf + 63),
    r("phase-publish"; "stage-publish"; "Phase"; "Publish"; $tf + 63; $tf + 103),
    r("job-publish"; "phase-publish"; "Job"; "Publish"; $tf + 68; $tf + 103),
    r("p1"; "job-publish"; "Task"; "Publish artifacts"; $tf + 70; $tf + 101)
  ] end)) }
}
JQ
  jq -n --argjson id "$1" --argjson q "$2" --argjson iq "$3" --argjson idur "$4" --argjson rdur "$5" \
    --argjson live "${6:-false}" -f "$tm/fixture.jq" >"$tm/fixture-$1.json"
  jq '.run' "$tm/fixture-$1.json" >"$tm/run-$1.json"
  jq '.timeline' "$tm/fixture-$1.json" >"$tm/timeline-$1.json"
}

tm_fixture 100 120 120 480 90
# A window of five runs of one pipeline: run 104 is the one-off slow Integration run (900 s).
tm_fixture 101 120 120 480 90
tm_fixture 102 60 100 470 88
tm_fixture 103 200 130 500 95
tm_fixture 104 90 110 900 91
tm_fixture 105 100 115 490 89
tm_fixture 200 120 120 480 90 true
jq -s '{count: length, value: .}' "$tm/run-105.json" "$tm/run-104.json" "$tm/run-103.json" "$tm/run-102.json" "$tm/run-101.json" >"$tm/list.json"
echo '{"count":1,"value":[{"id":7,"name":"Team-CI"}]}' >"$tm/definitions.json"
echo '{"Build": [], "Test": ["Build"], "Scan": ["Build"], "Publish": ["Test", "Scan"]}' >"$tm/deps.json"

timing() {
  env -u HARNESS_AZURE_CONFIG_DIR PATH="$tmp/timing-bin:$PATH" STUB_DIR="$tm" \
    "$h/tools/azure-devops/ado-run-timing.sh" https://dev.azure.com/org "Team Project" "$@"
}

# A single finished run, with the declared dependencies.
expect 0 "single run reports" timing 100 --deps "$tm/deps.json"
timing 100 --deps "$tm/deps.json" >"$tm/single.txt" 2>&1
timing 100 --deps "$tm/deps.json" --json >"$tm/single.json"
expect 0 "report separates queue from execution" grep -q 'waiting to start' "$tm/single.txt"
expect 0 "report shows agent queue next to execution per job" grep -qE 'AGENT QUEUE +EXECUTION' "$tm/single.txt"
expect 0 "report names the critical path edges" grep -q 'Critical path (declared edges)' "$tm/single.txt"
expect 0 "wall clock, queue before start and running time are measured" \
  jq -e '.totals.elapsed.median == 1087 and .totals.queueBeforeStart.median == 120 and .totals.running.median == 967' "$tm/single.json"
expect 0 "critical path is Compile, Integration, Publish: neither the sum of the stages (1355 s) nor the longest stage (600 s)" \
  jq -e '(.criticalPath.rows | map(.job)) == ["Compile","Integration","Publish"]
         and (.criticalPath.rows | map(.run) | add) + (.criticalPath.rows | map(.wait) | add) + .criticalPath.tailSec == 967
         and (.stages | map(.duration.median) | add) == 1355' "$tm/single.json"
expect 0 "critical path splits wait, agent queue and run per job" \
  jq -e '(.criticalPath.rows | map(.wait)) == [45,122,68] and (.criticalPath.rows | map(.queue)) == [40,120,5]
         and (.criticalPath.rows | map(.run)) == [215,480,35] and .criticalPath.tailSec == 2' "$tm/single.json"
expect 0 "critical path totals add up to the running time" \
  jq -e '.totals.criticalPathAgentQueue.median == 165 and .totals.criticalPathOtherWait.median == 72 and .totals.criticalPathExec.median == 730
         and (165 + 72 + 730) == .totals.running.median' "$tm/single.json"
expect 0 "Scan is off the path with 204 s of slack, Test is on it" \
  jq -e '(.stages[] | select(.stage == "Scan")) as $s | (.stages[] | select(.stage == "Test")) as $t
         | $s.onPathRuns == 0 and $s.slackMedian == 204 and $t.onPathRuns == 1' "$tm/single.json"
expect 0 "approval wait is its own number, not execution" \
  jq -e '(.stages[] | select(.stage == "Publish") | .checksWaitMedian) == 60' "$tm/single.json"
expect 0 "job queue and execution are separate fields" \
  jq -e '(.jobs[] | select(.job == "Test > Integration")) | .agentQueue.median == 120 and .execution.median == 480' "$tm/single.json"
expect 0 "tasks are sorted worst first, duplicate names are numbered" \
  jq -e '.tasks[0].task == "Test > Integration > Run integration tests" and .tasks[0].duration.median == 475
         and ([.tasks[].task] | index("Build > Compile > Bash #2") != null)' "$tm/single.json"
expect 0 "control characters in task names are stripped" bash -c "! grep -q \$'\\x1b' '$tm/single.txt' '$tm/single.json' && ! grep -q \$'\\t' '$tm/single.txt'"
expect 0 "a single run carries the one-sample caveat" grep -q 'One run is one sample' "$tm/single.txt"

# Without --deps the path is inferred from timing; the result is the same on this run and says so.
timing 100 --json >"$tm/inferred.json"
expect 0 "without --deps the edges are labelled inferred and the path matches" \
  jq -e '.criticalPath.source == "inferred" and (.criticalPath.rows | map(.job)) == ["Compile","Integration","Publish"]
         and (.notes | map(test("inferred")) | any)' "$tm/inferred.json"
echo '{"Test": ["Build"]}' >"$tm/partial.json"
timing 100 --deps "$tm/partial.json" --json >"$tm/partial-out.json"
expect 0 "a partial --deps file is labelled mixed" jq -e '.criticalPath.source == "mixed"' "$tm/partial-out.json"
echo '{"Build": [], "Test": ["Build"], "Scan": ["Build"], "Publish": ["Scan"]}' >"$tm/scanpath.json"
timing 100 --deps "$tm/scanpath.json" --json >"$tm/scanpath-out.json"
expect 0 "the path follows the declared edges, not the timing" \
  jq -e '(.criticalPath.rows | map(.job)) == ["Compile","Scan","Publish"]' "$tm/scanpath-out.json"

# A window of runs: median and spread per task, so a one-off slow run is not a trend.
expect 0 "window by pipeline name" timing pipeline:Team-CI --last 5 --deps "$tm/deps.json"
timing pipeline:Team-CI --last 5 --deps "$tm/deps.json" >"$tm/window.txt" 2>&1
timing pipeline:7 --last 5 --branch main --deps "$tm/deps.json" --json >"$tm/window.json"
expect 0 "window has five runs" jq -e '.mode == "window" and .runCount == 5' "$tm/window.json"
expect 0 "queue before start is a median over the window (60 90 100 120 200)" \
  jq -e '.totals.queueBeforeStart.median == 100 and .totals.queueBeforeStart.min == 60 and .totals.queueBeforeStart.max == 200' "$tm/window.json"
expect 0 "Integration task: median 485 s, max 895 s from the one-off, spread 89 %" \
  jq -e '(.tasks[] | select(.task == "Test > Integration > Run integration tests") | .duration)
         | .median == 485 and .min == 465 and .max == 895 and .spreadPct == 89' "$tm/window.json"
expect 0 "a stable task has a small spread (Restore 7.8 %)" \
  jq -e '(.tasks[] | select(.task == "Build > Compile > Restore") | .duration) | .median == 90 and .spreadPct == 8' "$tm/window.json"
expect 0 "agent queue spread is reported per job" \
  jq -e '(.jobs[] | select(.job == "Test > Integration") | .agentQueue) | .median == 115 and .max == 130' "$tm/window.json"
expect 0 "critical path comes from the run closest to the median, not the outlier" \
  jq -e '.criticalPath.runId == 101 and (.runs | map(.id) | index(104) != null)' "$tm/window.json"
expect 0 "on-path frequency is counted across runs" \
  jq -e '(.stages[] | select(.stage == "Test") | .onPathRuns) == 5 and (.stages[] | select(.stage == "Scan") | .onPathRuns) == 0' "$tm/window.json"
expect 0 "window report has median, min, max and spread columns" grep -qE 'MEDIAN +MIN +MAX +SPREAD' "$tm/window.txt"
expect 0 "window report names the window" grep -q 'Window: 5 runs' "$tm/window.txt"
expect 0 "window requests succeeded runs of the resolved definition" \
  bash -c "grep -q 'definitions=7' '$tm/curl.log' && grep -q 'resultFilter=succeeded' '$tm/curl.log' && grep -q 'branchName=refs/heads/main' '$tm/curl.log'"
timing pipeline:7 --result any --json >/dev/null
expect 0 "--result any drops the result filter" bash -c "tail -n 12 '$tm/curl.log' | grep 'definitions=7' | tail -n 1 | grep -vq resultFilter"

# A run still in progress: partial numbers, exit 2 like ado-run-watch.sh.
expect 2 "run in progress exits 2" timing 200 --deps "$tm/deps.json"
timing 200 --deps "$tm/deps.json" >"$tm/live.txt" 2>&1
timing 200 --deps "$tm/deps.json" --json >"$tm/live.json"
expect 0 "in-progress report says it is partial" grep -q 'still in progress' "$tm/live.txt"
expect 0 "in-progress json flags it and keeps the open job" \
  jq -e '.inProgress == true and ((.jobs[] | select(.job == "Test > Integration")) | .agentQueue.median == 120)' "$tm/live.json"
expect 2 "run in progress exits 2 with --json" timing 200 --json

# Refusals and errors.
expect 4 "a run id that does not exist exits 4" timing 999
expect 3 "run id must be numeric" timing not-a-run
expect 3 "organization must be dev.azure.com" env PATH="$tmp/timing-bin:$PATH" STUB_DIR="$tm" "$h/tools/azure-devops/ado-run-timing.sh" https://example.com p 100
expect 3 "window options need a pipeline target" timing 100 --last 5
expect 3 "window above 30 runs is refused" timing pipeline:7 --last 31
expect 3 "unknown option is refused" timing 100 --queue
expect 3 "a --deps file that is not valid JSON is refused" bash -c "echo nope >'$tm/bad.json'; PATH='$tmp/timing-bin:$PATH' STUB_DIR='$tm' '$h/tools/azure-devops/ado-run-timing.sh' https://dev.azure.com/org p 100 --deps '$tm/bad.json'"
expect 3 "a pipeline name with odd characters is refused" timing 'pipeline:a;b'
expect 3 "a pipeline name that matches nothing is refused" bash -c "echo '{\"value\":[]}' >'$tm/definitions.json'; PATH='$tmp/timing-bin:$PATH' STUB_DIR='$tm' '$h/tools/azure-devops/ado-run-timing.sh' https://dev.azure.com/org p pipeline:Nope"

# Read-only: the stubs saw only GETs and only the token request on az.
expect 0 "curl never wrote (no -X, -d or --data)" bash -c "! grep -qE '(^| )(-X|-d|--data|--request)( |$)' '$tm/curl.log'"
expect 0 "az was only asked for a token" bash -c "! grep -v '^account get-access-token' '$tm/az.log'"
