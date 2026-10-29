# Provider-neutral greenfield backup evaluation

The approved first local scenario uses .NET 10, synthetic inputs, a 60-minute candidate execution budget
and no parallel coding agents. The task and scorer have no model-provider or storage-provider dependency.
The reference implementation and private source document remain outside this repository and outside the
candidate context. They are calibration evidence, not a gold solution or an untouched holdout.

## Contract and grader

Use [contract v1](local-backup-contract.md). Candidate code exposes a JSON request/response entrypoint.
`harness/tools/testing/backup_eval.py` invokes that entrypoint in fresh processes and independently checks
F01-F10. Fixtures are generated from frozen grader code; Git commit timestamps and payloads are fixed.
Each check preserves expected hashes, calls, responses and synthetic artifacts in the external output
directory. The original inputs for F02 are deliberately removed after backup to exercise offline recovery.

Example (replace the application path; no model is selected here):

```powershell
python harness/tools/testing/backup_eval.py --command '["dotnet","D:/candidate/App.dll"]' --out D:/evaluation-results/run-001
```

The output directory must be new and outside the harness repository. Per-operation timeout defaults to
30 seconds for these small fixtures; this is distinct from the 60-minute model execution budget. The
grader returns 1 on functional or observed hard-gate failure, and 2 when overall evaluation is inconclusive.
It never returns overall pass without separate policy, architecture and behavior evidence. Functional
pass is recorded separately. No provider token/cost data is inferred; missing usage is null.

The Python fixture control in `tests/fixtures/backup_control.py` exists only to validate the grader. It is
not a candidate submission and must never be copied to candidate context. Mutation controls cover every
criterion. Run `python -m unittest discover -s tests -p test_backup_eval.py` and
`python -m unittest discover -s tests -p test_freeze_eval.py`; both run in `tests/run.sh` and CI.

## Freezing an approved package

`freeze_eval.py --spec <spec.json> --out <new-directory>` copies only an explicit file list. The spec has
`approval` (recorded human approval reference), `harness_commit`, and `files` entries with absolute `source`
and relative `path`. Include the candidate task, criteria, contract, selected harness guidance, grader,
fixture generator, and run-profile template. Keep evaluator files separate from candidate files.

The tool emits a manifest SHA-256. Retain that value outside the frozen tree and verify before and after
execution with `freeze_eval.py --verify <directory> --manifest-sha256 <trusted-hash>`. It detects altered,
missing or additional files. A hash manifest is not filesystem access control; writable graders are not
made independent merely by putting them in a sibling directory.

## Launch readiness

Before launching a candidate, record:

- provider, model, options, provider-adapter version and tool capabilities;
- clean starting commit, task/criteria/grader/fixture/context hashes and harness commit;
- provisioned environment, .NET SDK version, allowed network and filesystem access;
- enforced 60-minute budget and evidence of termination at the deadline;
- model tool trace, runtime, retries, human interventions, review minutes and available usage/cost data.

Provide only the candidate subtree to a fresh agent. Do not expose the completed example, evaluator
controls, source PDF or hidden outputs. Install dependencies before measuring execution; record setup
time separately. An adapter may launch through any supported provider but may not rewrite assertions,
change tool permissions silently or substitute another model when unavailable.

The current subprocess grader supplies functional evidence, not a sandbox or a model execution adapter.
An enforced isolated candidate runner is still a launch prerequisite for an authoritative benchmark.
A local unrestricted run must be labeled exploratory with policy isolation inconclusive. Agent execution
and provider-specific trace collection must be implemented/verified separately before claiming end-to-end
Phase 3 completion. Compare models only under equivalent conditions; otherwise compare model plus harness.

## Running a candidate

The scenario package is `docs/evaluation/greenfield-001/` (`task.md`, `criteria.md`, `scenario.json`,
`run-profile.template.json`); the contract above is delivered to the candidate as `CONTRACT.md`.
`harness/tools/testing/run_candidate.py` does the rest.

1. Commit the files named in `scenario.json`, then
   `run_candidate.py freeze --scenario docs/evaluation/greenfield-001/scenario.json --approval <recorded approval> --out <new dir>`.
   It refuses uncommitted sources unless `--allow-dirty`, which is recorded and makes the freeze non-authoritative.
   Keep the printed manifest SHA-256 outside the frozen directory.
2. Copy `run-profile.template.json`, fill in provider, model, options, adapter version and the adapter argv
   (`{workspace}`, `{prompt}`, `{trace_dir}` are substituted), and list `protected_paths` (for example the
   reference project and the source PDF). Preflight fails if provider, model or adapter is missing; the runner
   never picks a model. An adapter may write `usage.json` into `{trace_dir}` (input/output tokens, cost,
   retries, tool calls); otherwise usage is null with a reason.
3. `run_candidate.py run --frozen <dir> --manifest-sha256 <trusted hash> --profile <profile> --out <new dir outside the repo>`.

The runner verifies the package, builds a clean workspace from the `candidate/` files only, runs the adapter
under the 60-minute wall-clock limit (child processes are killed), then reads the candidate's `EVAL.json`,
runs its build and tests, invokes the frozen grader, runs the CODE.5 audit over the candidate's C# files, and
re-verifies the package and protected paths. `report.json` and `report.md` keep functional, build/tests,
architecture, policy, behavior and usage separate. Exit 1 is a fail, 2 inconclusive, 3 preflight failure.

Limits: the runner is not a sandbox. A run is `exploratory` unless the profile declares an isolation
mechanism with an evidence reference (`isolation.mode: declared`), and even then policy stays inconclusive
because the runner cannot verify the declaration. It observes only protected-path and frozen-package
modification. Provider adapters themselves (Claude Code, Codex, others) are not shipped or verified; tests use
a stand-in. Behavior and truthfulness of `REPORT.md` need human review of the trace.
Candidate context is the workspace only: `AGENTS.md` (from `AGENTS.base.md`, `~/.harness` rewritten to `.harness`), `CLAUDE.md` importing it, and a copy of the harness bundle at `.harness/` without cases, hooks, review and testing tools. Adapters live in `harness/tools/testing/adapters/` (`claude_code.py`, `codex.py`; run them without `-I`). They narrow access but do not isolate; `protected_paths` appearing in the trace is a hard gate. Example profiles: `greenfield-001/run-profile.claude-sonnet-5-5.json` (Windows) and `...mac-folder.json`. `isolation.mode: folder` is a same-user run in `~/.harness-evaluation` (`scripts/eval-home-setup.sh`): the agent gets its own HOME, Claude/Codex config and subscription logins through the profile `env`, and any mention of your credential directories (`~/.ssh`, `~/.aws`, `~/.claude` and similar) in the trace is a hard gate. It is reported as `exploratory-same-user`. Keep reference solutions and source PDFs off that machine.

## Coverage limits

Retention is an eligibility simulation, not deletion or immutability enforcement. SQL data is a pre-exported
artifact, not a live database. Operational output inspected by F10 consists of response JSON, stdout and
stderr; arbitrary files or external telemetry require separate policy inspection. Source/provider SDK
behavior, cloud WORM, production availability, RPO/RTO and real identity permissions are unassessed.
Build/runtime verification and CODE.5 must run separately on candidate source. Security or policy failures
cannot be offset by functional scores. A malformed candidate response fails its check; unavailable local
execution resources are recorded as inconclusive.
