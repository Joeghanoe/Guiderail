# Evaluation cases and the train / validation / holdout split

Cases are brownfield: a change task on an existing codebase, with hidden acceptance criteria. Greenfield scenarios have a [separate index](../greenfield/README.md). [run_brownfield.py](../../harness/tools/testing/run_brownfield.py) runs validation cases (see below).

To register existing projects through symlinks or copies, freeze their sources and document known gaps, follow the [reference project validation workflow](../reference-projects.md). It also explains how the local project registry connects to these executable cases.

| Role | What it is for | Where it lives | May teach the harness |
| --- | --- | --- | --- |
| train | source of examples (`harness/examples/`) | no cases | yes |
| validation | choose between harness changes; run often | `benchmarks/cases/validation/<id>/` | never |
| holdout | sealed; run at release only, never read while tuning | `~/.harness-evaluation/holdout/` (outside the repo) | never |

- One component has one role. A pattern seen in a train component may reappear in a validation case; that tests generalisation. Do not turn a validation or holdout case into an example, a rule edit or a template.
- A case holds `task.md` (what the agent is asked), `criteria.md` (hidden checks and rule IDs), `case.json`, and `snapshot.json` (neutral file paths plus sha256, because the sources have no Git metadata).
- The map from neutral aliases to real paths is private (`~/.harness-evaluation/private/`) and is the only place real names appear. Repo content carries none ([project-terms.txt](../../harness/templates/project-terms.txt)).
- Boundary examples need a human owner. Candidates without one are parked in `~/.harness-evaluation/pending-boundary/` until a person accepts the deviation.

## Validation case index

Evaluator navigation for the cases below. The runner copies the task and pinned source files into the candidate workspace alongside the harness. This index and hidden criteria remain outside that workspace.

| Case | Assignment | Candidate input | Evaluator input | Configuration |
| --- | --- | --- | --- | --- |
| v-aq-back-v-01 | Add a dataset: advisor recommendations | [Task](validation/v-aq-back-v-01/task.md) | [Hidden criteria](validation/v-aq-back-v-01/criteria.md) | [Case](validation/v-aq-back-v-01/case.json), [snapshot](validation/v-aq-back-v-01/snapshot.json) |
| v-aq-back-v-02 | Resource health is missing for some subscriptions and nothing was red | [Task](validation/v-aq-back-v-02/task.md) | [Hidden criteria](validation/v-aq-back-v-02/criteria.md) | [Case](validation/v-aq-back-v-02/case.json), [snapshot](validation/v-aq-back-v-02/snapshot.json) |
| v-aq-back-v-03 | Make the throttle window testable | [Task](validation/v-aq-back-v-03/task.md) | [Hidden criteria](validation/v-aq-back-v-03/criteria.md) | [Case](validation/v-aq-back-v-03/case.json), [snapshot](validation/v-aq-back-v-03/snapshot.json) |
| v-aq-back-v-04 | Wrong identity for the data lake after a settings change | [Task](validation/v-aq-back-v-04/task.md) | [Hidden criteria](validation/v-aq-back-v-04/criteria.md) | [Case](validation/v-aq-back-v-04/case.json), [snapshot](validation/v-aq-back-v-04/snapshot.json) |
| v-aq-front-01 | The customer list stops at 50 | [Task](validation/v-aq-front-01/task.md) | [Hidden criteria](validation/v-aq-front-01/criteria.md) | [Case](validation/v-aq-front-01/case.json), [snapshot](validation/v-aq-front-01/snapshot.json) |
| v-aq-front-02 | Stop reading status codes out of error messages | [Task](validation/v-aq-front-02/task.md) | [Hidden criteria](validation/v-aq-front-02/criteria.md) | [Case](validation/v-aq-front-02/case.json), [snapshot](validation/v-aq-front-02/snapshot.json) |
| v-aq-front-03 | Show when the health picture is incomplete | [Task](validation/v-aq-front-03/task.md) | [Hidden criteria](validation/v-aq-front-03/criteria.md) | [Case](validation/v-aq-front-03/case.json), [snapshot](validation/v-aq-front-03/snapshot.json) |
| v-aq-front-04 | The configure page is one 1000-line file | [Task](validation/v-aq-front-04/task.md) | [Hidden criteria](validation/v-aq-front-04/criteria.md) | [Case](validation/v-aq-front-04/case.json), [snapshot](validation/v-aq-front-04/snapshot.json) |
| v-b2b-ing-01 | Accept CSV submissions without changing other limits | [Task](validation/v-b2b-ing-01/task.md) | [Hidden criteria](validation/v-b2b-ing-01/criteria.md) | [Case](validation/v-b2b-ing-01/case.json), [snapshot](validation/v-b2b-ing-01/snapshot.json) |
| v-hub-plat-01 | Remove sensitive content from dead letters and telemetry | [Task](validation/v-hub-plat-01/task.md) | [Hidden criteria](validation/v-hub-plat-01/criteria.md) | [Case](validation/v-hub-plat-01/case.json), [snapshot](validation/v-hub-plat-01/snapshot.json) |
| v-hub-plat-02 | Extend employee fields and assess the contract-end-date request | [Task](validation/v-hub-plat-02/task.md) | [Hidden criteria](validation/v-hub-plat-02/criteria.md) | [Case](validation/v-hub-plat-02/case.json), [snapshot](validation/v-hub-plat-02/snapshot.json) |
| v-hub-plat-03 | Configure delivery attempts for one connector | [Task](validation/v-hub-plat-03/task.md) | [Hidden criteria](validation/v-hub-plat-03/criteria.md) | [Case](validation/v-hub-plat-03/case.json), [snapshot](validation/v-hub-plat-03/snapshot.json) |

## Running a validation case

```bash
python3 harness/tools/testing/run_brownfield.py run \
  --case benchmarks/cases/validation/<id> --profile <run-profile.json> --out ~/.harness-evaluation/runs/<name>
python3 harness/tools/testing/run_brownfield.py grade --case ... --run ~/.harness-evaluation/runs/<name> --profile <run-profile.json>
```

- Only `validation` cases run; holdout is refused. The workspace is built from the private source map and each file is checked against its pinned sha256; a changed source stops the run.
- The candidate sees `TASK.md`, the harness and the snapshot, never `criteria.md`. A separate grader session judges each criterion from the saved diff (`grade` replays it without rerunning the candidate). The run profile may add `"grader": {"argv": [...]}` (stdin is the prompt); the default is `claude -p` with the profile's model.
- CODE.5 runs in change mode against the snapshot, so introduced findings are scored and inherited ones are only counted. Build and tests stay inconclusive because the snapshot is a subset of the project.
- Rubric verdicts are LLM-judged; treat a single run as one sample (ADR 0005: repeat where feasible).

## Diagnosing a run

```bash
python3 harness/tools/testing/diagnose_run.py propose --run ~/.harness-evaluation/runs/<name>
python3 harness/tools/testing/diagnose_run.py record --run ... --finding D01 --class evaluator-defect --by <reviewer> --note "..."
```

`propose` reads the report and writes `diagnosis.json` with a suggested class per doubtful result: project defect, evaluator defect, incomplete principle, model or harness failure, or insufficient evidence. Suggestions are leads; only `record` by a named person classifies. Nothing here edits rules, criteria or graders (those changes go through review).
