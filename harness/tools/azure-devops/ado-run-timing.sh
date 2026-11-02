#!/usr/bin/env bash
# Measure where an Azure DevOps pipeline run spends its time: total wall clock, queue time kept apart from
# execution time, stage / job / task durations worst first, the critical path through the stage dependencies,
# and, over a window of runs, the median and spread per task. Replaces reading the run page and guessing.
#
# Tool contract (Vegviser AI Tool Boundary)
#   Classification:  Read. GET only, fixed host (dev.azure.com): the build, the build list, the build timeline
#                    and the build definition list. It never calls the log endpoints, never queues, retries or
#                    cancels a run (CLD.1, CLD.2).
#   Owner:           team:teamvalue-aicoe. Version: the harness commit in .harness/VERSION.
#   Caller identity: the user's own `az` login, see ado-common.sh. The token goes to curl on stdin and is never
#                    printed. The agent never logs in (CLD.1).
#   Inputs:          <organization> <project> <runId | pipeline:<id|name>> [--last N=10] [--branch B]
#                    [--result succeeded|any] [--deps FILE] [--top N=15] [--json].
#                    runId is the numeric run id, not the build number. pipeline:<...> measures the newest N
#                    completed runs of that pipeline (succeeded only, unless --result any). --deps is a local
#                    JSON file of declared dependencies, see below.
#   Results:         a readable report on stdout, or JSON with --json. Exit 0 measured, 2 the single run is
#                    still in progress (the report is partial), 3 refused, 4 HTTP >= 400 (a run id that does
#                    not exist is a 404, so exit 4).
#   Side effects:    none. Reads no log text, so no log content is printed. Prints durations plus stage, job and
#                    task names, which come from the pipeline definition and are untrusted data (SEC.1: a pull
#                    request can rename a task); control characters are stripped and names cut at 120
#                    characters. Prints no requester, variables, secure files or connections (SEC.2).
#   Review trigger:  a new endpoint, a field read from run metadata that names a person, or any endpoint that
#                    returns variables, secure files or connections.
#
# Why the critical path needs --deps: the build timeline carries start and finish times but not `dependsOn`.
# With --deps FILE (a JSON object, stage identifier to the list of stages it depends on, written from the
# pipeline YAML; `"Stage/Job": [...]` does the same for jobs inside a stage; `[]` means no dependency, and a
# stage without `dependsOn` in YAML depends on the stage above it) the path follows the declared edges: from the
# last stage to finish, step back to the declared dependency that finished last, and repeat. A node missing from
# the file, or no file, falls back to timing: the predecessor is the node that finished last at or before the node
# started (1 second of tolerance). The report says which of the two it used; inferred edges can miss a
# dependency that did not bind on this run.
#
# Usage:   ado-run-timing.sh https://dev.azure.com/teamvalue Bizure 26122
#          ado-run-timing.sh https://dev.azure.com/teamvalue Bizure pipeline:Bizure-CI --last 10 --branch main
#          ado-run-timing.sh https://dev.azure.com/teamvalue Bizure 26122 --deps /tmp/deps.json --json
set -euo pipefail

tool="ado-run-timing"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=ado-common.sh
source "$here/ado-common.sh"

usage="usage: ado-run-timing.sh <organization-url> <project> <runId|pipeline:id-or-name> [--last N] [--branch B] [--result succeeded|any] [--deps FILE] [--top N] [--json]"
[[ $# -ge 3 ]] || ado_refuse "$usage"
org_arg="$1"
project_arg="$2"
target="$3"
shift 3

as_json=0
last=10
branch=""
result_filter="succeeded"
top=15
deps_file=""
window_option=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --json)
      as_json=1
      shift
      ;;
    --last | --branch | --result | --deps | --top)
      [[ $# -ge 2 ]] || ado_refuse "$1 needs a value. $usage"
      case "$1" in
        --last) last="$2" window_option=1 ;;
        --branch) branch="$2" window_option=1 ;;
        --result) result_filter="$2" window_option=1 ;;
        --deps) deps_file="$2" ;;
        --top) top="$2" ;;
      esac
      shift 2
      ;;
    *) ado_refuse "unknown option '$1'. $usage" ;;
  esac
done

[[ "$last" =~ ^[0-9]+$ ]] || ado_refuse "--last must be a number."
((last >= 1 && last <= 30)) || ado_refuse "--last must be 1 to 30; each run costs two GETs."
[[ "$top" =~ ^[0-9]+$ ]] || ado_refuse "--top must be a number."
[[ "$result_filter" == "succeeded" || "$result_filter" == "any" ]] || ado_refuse "--result must be succeeded or any."
[[ -z "$branch" || "$branch" =~ ^[A-Za-z0-9._/-]+$ ]] || ado_refuse "branch has characters outside A-Za-z0-9._/-."

if [[ "$target" == pipeline:* ]]; then
  pipeline="${target#pipeline:}"
  [[ "$pipeline" =~ ^[0-9]+$ || "$pipeline" =~ ^[A-Za-z0-9\ ._()-]+$ ]] ||
    ado_refuse "pipeline must be the numeric definition id or a name of A-Za-z0-9 space . _ ( ) -; use the id otherwise."
  mode="window"
else
  [[ "$target" =~ ^[0-9]+$ ]] || ado_refuse "run must be the numeric run id (not the build number) or pipeline:<id|name>."
  ((window_option == 0)) || ado_refuse "--last, --branch and --result apply to pipeline:<id|name> only."
  mode="single"
fi

deps_json="{}"
if [[ -n "$deps_file" ]]; then
  [[ -f "$deps_file" ]] || ado_refuse "--deps file not found."
  deps_json="$(jq -c '.' "$deps_file" 2>/dev/null)" || ado_refuse "--deps file is not valid JSON."
  jq -e 'type == "object" and all(.[]; type == "array" and all(.[]; type == "string"))' <<<"$deps_json" >/dev/null ||
    ado_refuse "--deps must be a JSON object whose values are lists of names, for example {\"Test\": [\"Build\"]}."
fi

ado_init "$org_arg" "$project_arg"
builds="$ado_org/$ado_project/_apis/build/builds"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# ---------------------------------------------------------------------------------------------------------
# jq program 1: one run + its timeline -> one model. Everything is measured here; nothing is printed raw.
# ---------------------------------------------------------------------------------------------------------
cat >"$work/model.jq" <<'JQ'
def frac: (capture("\\.(?<f>[0-9]+)Z$").f // "0") | ("0." + .) | tonumber;
def ts: if . == null then null else (try ((sub("\\.[0-9]+Z$"; "Z") | fromdateiso8601) + frac) catch null) end;
def clean: tostring | gsub("[[:cntrl:]]"; " ") | .[0:120];
def pos: if . == null then null elif . < 0 then 0 else . end;
def tol: 1;

. as [$run, $tl]
| ($tl.records // []) as $recs
| ($recs | map({key: .id, value: .}) | from_entries) as $by
| ($run.queueTime | ts) as $q
| ($run.status != "completed") as $live
| (($run.startTime | ts) // $q) as $rs
| (if $live then $now else (($run.finishTime | ts) // $now) end) as $rf
| def up($t): if . == null then null elif .type == $t then . else ($by[.parentId // ""] | up($t)) end;
  def base: {
    id, type,
    key: ((.identifier // .name) | clean), name: (.name | clean),
    start: (.startTime | ts),
    finish: ((.finishTime | ts) // (if .state == "inProgress" then $now else null end)),
    state: (.state // "-"), result: (.result // "-"),
    open: (.finishTime == null and .state == "inProgress")
  };
  def ok: select(.start != null and .finish != null);
  # Predecessor of $n among $nodes: the declared dependency that finished last, or (no declaration) the node that
  # finished last at or before $n started. $seen guards against a cycle in a hand-written deps file.
  def pred($nodes; $n; $seen):
    if $n.decl != null then
      { p: ([ $nodes[] | select(. as $c | ($seen | index($c.id)) == null)
              | select(. as $c | $n.decl | any(.[]; . == $c.key or . == $c.name)) ] | max_by(.finish)),
        via: "declared" }
    else
      { p: ([ $nodes[] | select(. as $c | ($seen | index($c.id)) == null)
              | select(.start < $n.start and .finish <= $n.start + tol) ] | max_by(.finish)),
        via: "inferred" }
    end;
  def walk($nodes; $seen):
    . as $n | pred($nodes; $n; $seen) as $r
    | (if $r.p == null then [] else ($r.p | walk($nodes; $seen + [$r.p.id])) end) + [$n + {via: $r.via}];

  ([ $recs[] | select(.type == "Stage") | base | ok
     | . + {decl: ($deps[.key] // $deps[.name])} ]) as $stages
| ([ $recs[] | select(.type == "Job") | . as $rec | base
     | ($rec | up("Stage")) as $st
     | ([ $by[$rec.parentId // ""] | select(.type == "Phase") | (.startTime | ts) ] | .[0]) as $ps
     | . + { sid: ($st.id), stage: (if $st then ($st.name | clean) else "(none)" end),
             skey: (if $st then (($st.identifier // $st.name) | clean) else "(none)" end),
             phaseStart: $ps } ]) as $jobsAll
| ([ $jobsAll[] | ok
     | . + { decl: ($deps[.skey + "/" + .key] // $deps[.stage + "/" + .name]),
             queue: (if .phaseStart != null then ((.start - .phaseStart) | pos) else null end) } ]) as $jobs
| ([ $jobsAll[] | select(.start == null and .phaseStart != null) | {stage, job: .name, waited: ($now - .phaseStart)} ]) as $waiting
| ([ $recs[] | select(.type == "Task") | . as $rec | base | ok
     | ($rec | up("Job")) as $j | ($rec | up("Stage")) as $st
     | . + { order: ($rec.order // 0), jobId: ($j.id),
             job: (if $j then ($j.name | clean) else "(none)" end),
             stage: (if $st then ($st.name | clean) else "(none)" end),
             dur: (.finish - .start) } ]
   | sort_by(.start, .order)
   | group_by([.stage, .job, .name])
   | map(if length > 1 then [to_entries[] | .value + {name: (.value.name + " #" + ((.key + 1) | tostring))}] else . end)
   | add // []) as $tasks
| ([ $recs[] | select(.type == "Checkpoint") | . as $rec | base | ok
     | . + {sid: (($rec | up("Stage")) | .id)} ]) as $cps

# Critical path: stages first, then the jobs inside each stage on the path.
| ($stages | if length == 0 then null else max_by(.finish) end) as $ls
| (if $ls == null then [] else ($ls | walk($stages; [$ls.id])) end) as $schain
| (if ($schain | length) > 0 then
     ($schain | map(. as $s
       | [ $jobs[] | select(.sid == $s.id) ] as $js
       | if ($js | length) == 0
         then [{id: $s.id, stage: $s.name, job: "-", start: $s.start, finish: $s.finish, queue: null}]
         else ($js | max_by(.finish)) as $lj | ($lj | walk($js; [$lj.id])) end)
      | add)
   elif ($jobs | length) > 0 then
     ($jobs | max_by(.finish)) as $lj | ($lj | walk($jobs; [$lj.id]))
   else [] end) as $jchain
| (reduce $jchain[] as $r ({prev: $rs, rows: []};
     ([$r.start, .prev] | max) as $eff
     | ($eff - .prev) as $wait
     | .rows += [{ id: $r.id, stage: $r.stage, job: ($r.job // $r.name), wait: $wait,
                   queue: (if $r.queue == null then null else ([$r.queue, $wait] | min) end),
                   run: (($r.finish - $eff) | pos) }]
     | .prev = ([.prev, $r.finish] | max))) as $acc
| ($rf - $acc.prev | pos) as $tail
| ($acc.rows) as $rows
| ([$rows[].queue // 0] | add // 0) as $cpq
| ([$rows[].wait] | add // 0) as $cpw
| ([$rows[].run] | add // 0) as $cpx
| (if ($deps | length) == 0 or ($schain | length) == 0 then "inferred"
   elif ($schain | all(.decl != null)) then "declared"
   elif ($schain | any(.decl != null)) then "mixed"
   else "inferred" end) as $source
| ($stages | length > 0 and all(.decl != null)) as $complete
| {
    id: $run.id, number: ($run.buildNumber | clean), pipeline: ($run.definition.name // "?" | clean),
    status: $run.status, result: ($run.result // "-"), live: $live,
    queue: (($rs - $q) | pos), run: ($rf - $rs), elapsed: ($rf - $q),
    cp: { source: $source, rows: ($rows | map(del(.id))), tail: $tail,
          agentQueue: $cpq, otherWait: ($cpw - $cpq + $tail), exec: $cpx },
    stages: [ $stages[] | . as $s | {
        key, name, startOffset: (.start - $rs), dur: (.finish - .start),
        wait: ([ $cps[] | select(.sid == $s.id) | (.finish - .start) ] | add // 0),
        state, result, open,
        onPath: ($schain | any(.id == $s.id)),
        slack: (if $live or ($schain | any(.id == $s.id)) or ($complete | not) then null
                else ([ $stages[] | select(.decl | any(.[]; . == $s.key or . == $s.name)) | .start ] | min) as $next
                     | (($next // $rf) - $s.finish) | pos end) } ],
    jobs: [ $jobs[] | . as $j | {
        stage, name, startOffset: (.start - $rs), dur: (.finish - .start), queue, open,
        onPath: ($rows | any(.id == $j.id)) } ],
    tasks: [ $tasks[] | . as $t | {
        stage, job, name, dur, result, open, onPath: ($rows | any(.id == $t.jobId)) } ],
    waiting: $waiting
  }
JQ

# ---------------------------------------------------------------------------------------------------------
# jq program 2: models -> one aggregate: median and spread per stage, job and task, critical path of the run
# closest to the median, notes. A single run is the same shape with n = 1.
# ---------------------------------------------------------------------------------------------------------
cat >"$work/agg.jq" <<'JQ'
def r1: if . == null then null else ((. * 10 | round) / 10) end;
def absv: if . < 0 then -. else . end;
def med: sort | length as $n
  | if $n == 0 then null elif $n % 2 == 1 then .[($n - 1) / 2] else (.[$n / 2 - 1] + .[$n / 2]) / 2 end;
def pct($p): sort | length as $n
  | if $n == 0 then null
    else (($p / 100) * ($n - 1)) as $i | .[($i | floor)] as $lo | .[($i | ceil)] as $hi
      | $lo + ($hi - $lo) * ($i - ($i | floor)) end;
def stats: map(select(. != null)) as $v
  | if ($v | length) == 0 then null
    else ($v | med) as $m
      | { n: ($v | length), median: ($m | r1), min: ($v | min | r1), max: ($v | max | r1),
          p25: ($v | pct(25) | r1), p75: ($v | pct(75) | r1),
          spreadPct: (if $m > 0 then ((($v | max) - ($v | min)) / $m * 100 | round) else null end) } end;
def meds: map(select(. != null)) | if length == 0 then null else (med | r1) end;

. as $runs
| ($runs | length) as $n
| ($runs | map(.elapsed) | med) as $medEl
| ($runs | min_by((.elapsed - $medEl) | absv)) as $rep
| {
    mode: (if $n == 1 then "run" else "window" end),
    pipeline: $runs[0].pipeline,
    runCount: $n,
    inProgress: ($runs | any(.live)),
    runs: ($runs | map({id, number, result: (if .live then .status else .result end), live,
                        elapsedSec: (.elapsed | r1), queueSec: (.queue | r1)})),
    totals: {
      elapsed: ($runs | map(.elapsed) | stats),
      queueBeforeStart: ($runs | map(.queue) | stats),
      running: ($runs | map(.run) | stats),
      criticalPathAgentQueue: ($runs | map(.cp.agentQueue) | stats),
      criticalPathOtherWait: ($runs | map(.cp.otherWait) | stats),
      criticalPathExec: ($runs | map(.cp.exec) | stats)
    },
    criticalPath: { runId: $rep.id, source: $rep.cp.source,
                    rows: ($rep.cp.rows | map(.wait |= r1 | .queue |= r1 | .run |= r1)), tailSec: ($rep.cp.tail | r1),
                    runSec: ($rep.run | r1) },
    stages: ([ $runs[] | .stages[] ] | group_by(.key) | map({
        stage: .[0].name, runs: length, duration: (map(.dur) | stats), checksWaitMedian: (map(.wait) | meds),
        slackMedian: (map(.slack) | meds), onPathRuns: (map(select(.onPath)) | length) })
      | sort_by(-(.duration.median // 0))),
    jobs: ([ $runs[] | .jobs[] ] | group_by([.stage, .name]) | map({
        job: (.[0].stage + " > " + .[0].name), runs: length,
        agentQueue: (map(.queue) | stats), execution: (map(.dur) | stats),
        onPathRuns: (map(select(.onPath)) | length) })
      | sort_by(-(.execution.median // 0))),
    tasks: ([ $runs[] | .tasks[] ] | group_by([.stage, .job, .name]) | map({
        task: (.[0].stage + " > " + .[0].job + " > " + .[0].name), runs: length,
        duration: (map(.dur) | stats), onPathRuns: (map(select(.onPath)) | length) })
      | sort_by(-(.duration.median // 0))),
    waiting: $rep.waiting,
    notes: ([
      (if $n == 1 then "One run is one sample. Pipeline duration is partly noise (agent pool contention, cache hit variance); measure the pipeline over a window (pipeline:<id> --last 10) before concluding anything." else empty end),
      (if $n > 1 and $n < 5 then "Only \($n) runs: the spread is not meaningful below 5. Widen the window." else empty end),
      (if ($runs | any(.live)) then "The run is still in progress: open stages, jobs and tasks are measured up to now, and the critical path is provisional." else empty end),
      (if $rep.cp.source == "inferred" then "Critical path edges are inferred from timing (no complete --deps): a dependency that did not bind on this run is invisible. Pass --deps written from the pipeline YAML for the declared path." elif $rep.cp.source == "mixed" then "Critical path mixes declared and inferred edges; stages missing from --deps were inferred from timing." else empty end),
      (if ([ $runs[].jobs[] | select(.queue == null) ] | length) > 0 then "Some jobs have no Phase record, so their agent queue time is not measurable (shown as -)." else empty end),
      (if ($rep.waiting | length) > 0 then "\($rep.waiting | length) job(s) still waiting for an agent." else empty end),
      (if $n > 1 and ($runs | any(.result != "succeeded")) then "The window includes runs that did not succeed; tasks that never ran are absent from those runs (see the RUNS column)." else empty end)
    ])
  }
JQ

# ---------------------------------------------------------------------------------------------------------
# jq program 3: aggregate -> text report.
# ---------------------------------------------------------------------------------------------------------
cat >"$work/render.jq" <<'JQ'
def pad2: tostring | if length < 2 then "0" + . else . end;
def fmt: if . == null then "-"
  elif . < 1 then "\((. * 10 | round) / 10)s"
  else round as $s
    | if $s < 60 then "\($s)s"
      elif $s < 3600 then "\($s / 60 | floor)m\($s % 60 | pad2)s"
      else "\($s / 3600 | floor)h\($s % 3600 / 60 | floor | pad2)m" end end;
def pc: if . == null then "-" else "\(round)%" end;
def med: if . == null then null else .median end;
def table($align): . as $rows
  | ($rows | map(length) | max) as $nc
  | [ range(0; $nc) as $c | ($rows | map(.[$c] | tostring | length) | max) ] as $w
  | ([$rows[0], [ range(0; $nc) as $c | "-" * $w[$c] ]] + $rows[1:])
  | map( . as $row | [ range(0; $nc) as $c
        | ($row[$c] | tostring) as $s | ($w[$c] - ($s | length)) as $p
        | (if $align[$c:$c + 1] == "r" then ((" " * $p) + $s) else ($s + (" " * $p)) end) ]
      | join("  ") | sub("\\s+$"; "")) | .[];
def sec($t): "", "== \($t)";

. as $a
| ($a.runCount) as $n
| ($a.mode == "run") as $single
| def seen($k; $c): "\($c)/\($k)";
  def sp($s): if $s == null then "-" else ($s.spreadPct | pc) end;
  "Pipeline: \($a.pipeline)",
  (if $single then "Run \($a.runs[0].number) (id \($a.runs[0].id)): \($a.runs[0].result)"
   else "Window: \($n) runs, newest first, ids \($a.runs[:6] | map(.id | tostring) | join(", "))\(if $n > 6 then ", ..." else "" end)" end),

  sec("Where the time goes"),
  ( ( if $single
      then [["METRIC", "VALUE"]]
      else [["METRIC", "MEDIAN", "MIN", "MAX", "SPREAD"]] end
      + ( [ ["Queued to finished", $a.totals.elapsed],
            ["  waiting to start (queue, before any job ran)", $a.totals.queueBeforeStart],
            ["  running (start to finish)", $a.totals.running],
            ["Critical path: waiting for an agent", $a.totals.criticalPathAgentQueue],
            ["Critical path: approvals, checks, gaps", $a.totals.criticalPathOtherWait],
            ["Critical path: executing", $a.totals.criticalPathExec] ]
          | map(if $single then [.[0], (.[1].median | fmt)]
                else [.[0], (.[1].median | fmt), (.[1].min | fmt), (.[1].max | fmt), sp(.[1])] end) ) )
    | table("lrrrr") ),

  sec("Critical path (\($a.criticalPath.source) edges\(if $single then "" else ", run \($a.criticalPath.runId), the run closest to the median" end))"),
  ( ( [["STAGE", "JOB", "WAIT", "OF WHICH AGENT QUEUE", "RUN", "SHARE"]]
      + ( $a.criticalPath.rows | map([.stage, .job, (.wait | fmt), (.queue | fmt), (.run | fmt),
            (if $a.criticalPath.runSec > 0 then (((.wait + .run) / $a.criticalPath.runSec * 100) | pc) else "-" end)]) )
      + ( if $a.criticalPath.tailSec >= 1 then [["(after the last job)", "", ($a.criticalPath.tailSec | fmt), "", "", ""]] else [] end ) )
    | table("llrrrr") ),

  sec("Stages, slowest first"),
  ( ( if $single then [["STAGE", "DURATION", "CHECKS WAIT", "SLACK", "ON PATH"]]
      else [["STAGE", "MEDIAN", "MIN", "MAX", "SPREAD", "CHECKS WAIT", "SLACK", "ON PATH"]] end )
    + ( $a.stages | map(
        if $single then [.stage, (.duration.median | fmt), (.checksWaitMedian | fmt),
                         (if .onPathRuns > 0 then "critical" else (.slackMedian | fmt) end), seen($n; .onPathRuns)]
        else [.stage, (.duration.median | fmt), (.duration.min | fmt), (.duration.max | fmt), sp(.duration),
              (.checksWaitMedian | fmt), (if .onPathRuns == .runs then "critical" else (.slackMedian | fmt) end),
              seen($n; .onPathRuns)] end) )
    | table(if $single then "lrrrr" else "lrrrrrrr" end) ),

  sec("Jobs, slowest first (agent queue is waiting for an agent, execution is the job running)"),
  ( ( if $single then [["JOB", "AGENT QUEUE", "EXECUTION", "ON PATH"]]
      else [["JOB", "QUEUE MEDIAN", "QUEUE MAX", "EXEC MEDIAN", "EXEC MIN", "EXEC MAX", "SPREAD", "ON PATH"]] end )
    + ( $a.jobs | map(
        if $single then [.job, (.agentQueue | med | fmt), (.execution | med | fmt), seen($n; .onPathRuns)]
        else [.job, (.agentQueue | med | fmt), (.agentQueue.max? | fmt), (.execution.median | fmt),
              (.execution.min | fmt), (.execution.max | fmt), sp(.execution), seen($n; .onPathRuns)] end) )
    | table(if $single then "lrrr" else "lrrrrrrr" end) ),

  sec("Tasks, slowest first (top \($top))"),
  ( ( if $single then [["TASK", "DURATION", "ON PATH"]]
      else [["TASK", "MEDIAN", "MIN", "MAX", "SPREAD", "RUNS", "ON PATH"]] end )
    + ( $a.tasks[:$top] | map(
        if $single then [.task, (.duration.median | fmt), seen($n; .onPathRuns)]
        else [.task, (.duration.median | fmt), (.duration.min | fmt), (.duration.max | fmt), sp(.duration),
              seen($n; .runs), seen($n; .onPathRuns)] end) )
    | table(if $single then "lrr" else "lrrrrrr" end) ),

  sec("Largest tasks on the critical path (a task off the path changes nothing when it gets faster)"),
  ( ( [["TASK", "MEDIAN", "SHARE OF RUN", "ON PATH"]]
      + ( [ $a.tasks[] | select(.onPathRuns * 2 >= $n and .duration.median != null) ]
          | sort_by(-(.duration.median * .onPathRuns / $n)) | .[:5]
          | map([.task, (.duration.median | fmt),
                 (if $a.totals.running.median > 0 then (.duration.median / $a.totals.running.median * 100 | pc) else "-" end),
                 seen($n; .onPathRuns)]) ) )
    | table("lrrr") ),

  ( if ($a.waiting | length) > 0 then
      sec("Waiting for an agent now"), ($a.waiting[] | "\(.stage) > \(.job): \(.waited | fmt) so far") else empty end ),

  ( if ($a.notes | length) > 0 then sec("Notes"), ($a.notes[] | "- " + .) else empty end )
JQ

now="$(date -u +%s)"

# model_run <run-json-file> <run id>: fetches the timeline and appends one model to $work/models.jsonl.
model_run() {
  local rid="$2" tl="$work/timeline-$2.json"
  ado_get "$builds/$rid/timeline?api-version=7.1" >"$tl"
  jq -s --argjson now "$now" --argjson deps "$deps_json" -f "$work/model.jq" "$1" "$tl" >>"$work/models.jsonl"
}

: >"$work/models.jsonl"
if [[ "$mode" == "single" ]]; then
  ado_get "$builds/$target?api-version=7.1" >"$work/run.json"
  model_run "$work/run.json" "$target"
else
  def_id="$pipeline"
  if [[ ! "$pipeline" =~ ^[0-9]+$ ]]; then
    enc="$(jq -rn --arg n "$pipeline" '$n | @uri')"
    defs="$(ado_get "$ado_org/$ado_project/_apis/build/definitions?name=$enc&api-version=7.1")"
    count="$(jq -r '.value | length' <<<"$defs")"
    [[ "$count" == "1" ]] || ado_refuse "pipeline name matches $count definitions; pass the numeric definition id."
    def_id="$(jq -r '.value[0].id' <<<"$defs")"
  fi
  query="definitions=$def_id&statusFilter=completed&queryOrder=queueTimeDescending&\$top=$last&api-version=7.1"
  [[ "$result_filter" == "succeeded" ]] && query="$query&resultFilter=succeeded"
  [[ -n "$branch" ]] && query="$query&branchName=refs/heads/$branch"
  list="$(ado_get "$builds?$query")"
  [[ "$(jq -r '.value | length' <<<"$list")" -gt 0 ]] || ado_refuse "no completed run (result filter: $result_filter) found for that pipeline and branch."
  idx=0
  while IFS= read -r run_line; do
    idx=$((idx + 1))
    printf '%s' "$run_line" >"$work/run-$idx.json"
    model_run "$work/run-$idx.json" "$(jq -r '.id' <<<"$run_line")"
  done < <(jq -c '.value[]' <<<"$list")
fi

jq -s -f "$work/agg.jq" "$work/models.jsonl" >"$work/agg.json"

if ((as_json)); then
  cat "$work/agg.json"
else
  jq -r --argjson top "$top" -f "$work/render.jq" "$work/agg.json"
fi

# Exit 2 mirrors ado-run-watch.sh: the run had not ended, so the numbers are partial.
if [[ "$mode" == "single" && "$(jq -r '.inProgress' "$work/agg.json")" == "true" ]]; then
  exit 2
fi
