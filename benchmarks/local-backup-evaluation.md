# Provider-neutral greenfield backup evaluation

The approved first local scenario uses .NET 10, synthetic inputs, a 60-minute candidate execution budget and no parallel coding agents. The task and scorer have no model-provider or storage-provider dependency. The reference implementation and private source document remain outside this repository and outside the candidate context. They are calibration evidence, not a gold solution or an untouched holdout.

## Contract and grader

Use [contract v1](local-backup-contract.md). Candidate code exposes a JSON request/response entrypoint. `harness/tools/testing/backup_eval.py` invokes that entrypoint in fresh processes and independently checks F01-F10. Fixtures are generated from frozen grader code; Git commit timestamps and payloads are fixed. Each check preserves expected hashes, calls, responses and synthetic artifacts in the external output directory. The original inputs for F02 are deliberately removed after backup to exercise offline recovery.

Example (replace the application path; no model is selected here):

```powershell
python harness/tools/testing/backup_eval.py --command '["dotnet","D:/candidate/App.dll"]' --out D:/evaluation-results/run-001
```

The output directory must be new and outside the harness repository. Per-operation timeout defaults to 30 seconds for these small fixtures; this is distinct from the 60-minute model execution budget. The grader returns 1 on functional or observed hard-gate failure, and 2 when overall evaluation is inconclusive. It never returns overall pass without separate policy, architecture and behavior evidence. Functional pass is recorded separately. No provider token/cost data is inferred; missing usage is null.

The Python fixture control in `tests/fixtures/backup_control.py` exists only to validate the grader. It is not a candidate submission and must never be copied to candidate context. Mutation controls cover every criterion. Run `python -m unittest discover -s tests -p test_backup_eval.py` and `python -m unittest discover -s tests -p test_freeze_eval.py`; both run in `tests/run.sh` and CI.

## Freezing an approved package

`freeze_eval.py --spec <spec.json> --out <new-directory>` copies only an explicit file list. The spec has `approval` (recorded human approval reference), `harness_commit`, and `files` entries with absolute `source` and relative `path`. Include the candidate task, criteria, contract, selected harness guidance, grader, fixture generator, and run-profile template. Keep evaluator files separate from candidate files.

The tool emits a manifest SHA-256. Retain that value outside the frozen tree and verify before and after execution with `freeze_eval.py --verify <directory> --manifest-sha256 <trusted-hash>`. It detects altered, missing or additional files. A hash manifest is not filesystem access control; writable graders are not made independent merely by putting them in a sibling directory.

## Launch readiness

Before launching a candidate, record:

- provider, model, options, provider-adapter version and tool capabilities;
- clean starting commit, task/criteria/grader/fixture/context hashes and harness commit;
- provisioned environment, .NET SDK version, allowed network and filesystem access;
- enforced 60-minute budget and evidence of termination at the deadline;
- model tool trace, runtime, retries, human interventions, review minutes and available usage/cost data.

Provide only the candidate subtree to a fresh agent. Do not expose the completed example, evaluator controls, source PDF or hidden outputs. Install dependencies before measuring execution; record setup time separately. An adapter may launch through any supported provider but may not rewrite assertions, change tool permissions silently or substitute another model when unavailable.

The current subprocess grader supplies functional evidence, not a sandbox or a model execution adapter. An enforced isolated candidate runner is still a launch prerequisite for an authoritative benchmark. A local unrestricted run must be labeled exploratory with policy isolation inconclusive. Agent execution and provider-specific trace collection must be implemented/verified separately before claiming end-to-end Phase 3 completion. Compare models only under equivalent conditions; otherwise compare model plus harness.

## Running a candidate

The scenario package is `benchmarks/greenfield/001/` (`task.md`, `criteria.md`, `scenario.json`, `run-profile.template.json`); the contract above is delivered to the candidate as `CONTRACT.md`. `harness/tools/testing/run_candidate.py` does the rest.

1. Commit the files named in `scenario.json`, then `run_candidate.py freeze --scenario benchmarks/greenfield/001/scenario.json --approval <recorded approval> --out <new dir>`. It refuses uncommitted sources unless `--allow-dirty`, which is recorded and makes the freeze non-authoritative. Keep the printed manifest SHA-256 outside the frozen directory.
2. Copy `run-profile.template.json`, fill in provider, model, options, adapter version and the adapter argv (`{workspace}`, `{prompt}`, `{trace_dir}` are substituted), and list `protected_paths` (for example the reference project and the source PDF). Preflight fails if provider, model or adapter is missing; the runner never picks a model. An adapter may write `usage.json` into `{trace_dir}` (input/output tokens, cost, retries, tool calls); otherwise usage is null with a reason.
3. `run_candidate.py run --frozen <dir> --manifest-sha256 <trusted hash> --profile <profile> --out <new dir outside the repo>`.

The runner verifies the package, builds a clean workspace from the `candidate/` files only, runs the adapter under the 60-minute wall-clock limit (child processes are killed), then reads the candidate's `EVAL.json`, runs its build and tests, invokes the frozen grader, runs the CODE.5 audit over the candidate's C# files, and re-verifies the package and protected paths. `report.json` and `report.md` keep functional, build/tests, architecture, policy, behavior and usage separate. Exit 1 is a fail, 2 inconclusive, 3 preflight failure.

## Container runs (Rancher Desktop, recommended)

`isolation.mode: container` (profile `run-profile.claude-sonnet-5-5.container.json`) runs the agent, the candidate's build and tests, the grader and CODE.5 in throwaway `docker run --rm` containers. Use Rancher Desktop with the moby (dockerd) engine; on a Mac keep run folders under `/Users` so the VM can mount them.

1. `harness/tools/testing/container/build.sh` builds `harness-eval:local` (.NET 10 SDK, git, Python, Node, pinned `claude` and `codex`, non-root user). The CLI versions default to the ones installed on the host; the runner records the image ID with each run.
2. One-time subscription login into a dedicated volume (no API keys; your personal logins are not mounted): `run_candidate.py login --profile <profile> --tool claude` (then `/login`), and `--tool codex`. The volume is mounted only into the agent container, never into build, grade or CODE.5 containers. Codex's login callback needs port 1455, which the helper publishes on 127.0.0.1.
3. `run_candidate.py run ...` as before. Each phase sees only its mounts: agent gets workspace, trace dir, the adapters (read-only) and the login volume; build and tests get the workspace; the grader gets the workspace, the frozen package (read-only) and an output folder with no network; CODE.5 gets the workspace and the checker source (read-only), no network. Containers run with all capabilities dropped, no-new-privileges, memory, CPU and pid limits, and are killed on timeout. The report records image, limits and the exact mounts of every phase. Host git commands against the agent's repository run with hooks and fsmonitor disabled.

The container is constructed by the runner, so the mounts are known, but policy stays inconclusive: what the agent ran inside is not observed, and the network is open for the model API. Subscription runs report no dollar cost, and subscription rate limits can end a run early; treat that as infrastructure, not model, failure. The login volume persists between runs; the adapters disable session persistence, but start comparisons from the same volume state.

## Rescoring a saved run

`run_candidate.py rescore --run <run dir> --frozen <dir> --manifest-sha256 <hash> --profile <profile>` re-runs the entrypoint build, tests, grader and CODE.5 on a copy of the saved workspace and writes `rescore-<time>/report.json` inside the run directory. The agent is not rerun: execution, usage, behavior and agent-phase violations (frozen-package, protected-path) are carried over, and the report records the previous status and grader hash. Use it after improving a grader or the CODE.5 check, with a new frozen package built from the new commit. The original run evidence is never modified.

Limits: outside container mode the runner is not a sandbox. A run is `exploratory` unless the profile declares an isolation mechanism with an evidence reference (`isolation.mode: declared`), and even then policy stays inconclusive because the runner cannot verify the declaration. It observes only protected-path and frozen-package modification. Provider adapters (Claude Code, Codex) have only been tested against stand-in CLIs, and the container backend only against a stand-in `docker`; the first real run should be a short smoke test. Behavior and truthfulness of `REPORT.md` need human review of the trace. Candidate context is the workspace only: `AGENTS.md` (from `AGENTS.base.md`, `~/.golden-path-harness/harness` rewritten to `.harness`), `CLAUDE.md` importing it, and a copy of the harness bundle at `.harness/` without examples, hooks, review and testing tools. Adapters live in `harness/tools/testing/adapters/` (`claude_code.py`, `codex.py`; run them without `-I`). Example profiles: `../../benchmarks/greenfield/001/run-profile.claude-sonnet-5-5.container.json`, `...json` (Windows, no isolation) and `...mac-folder.json`. `isolation.mode: folder` is a same-user run in `~/.golden-path-harness/evaluation` (`infra/scripts/eval-home-setup.sh`): the agent gets its own HOME and config through the profile `env`, and any mention of your credential directories (`~/.ssh`, `~/.aws`, `~/.claude` and similar) in the trace is a hard gate. Keep reference solutions and source PDFs off the machine that runs the agent.

## Scenario 002 and the design dimension

`benchmarks/greenfield/002/` extends the task with the operational behaviour of the reference design: status, health, dry run, exclusions, an event catalogue and untrusted identifiers (F11-F16, [contract v2](local-backup-contract-v2.md)). F16 is a third security hard gate. The grader reads `evaluator/scenario.json` to know which criteria to run, so 001 stays F01-F10. Scenario 002 installs the base instructions as `AGENTS.base.md`, so the repo's own `AGENTS.md` is free. The architecture dimension now also reports `design-check.py` (D01-D09, `service` profile) and, from a Claude Code trace, how many source files were written before the design. Findings and the improvement loop: [greenfield/001/findings-run-1.md](greenfield/001/findings-run-1.md).

## Coverage limits

Retention is an eligibility simulation, not deletion or immutability enforcement. SQL data is a pre-exported artifact, not a live database. Operational output inspected by F10 consists of response JSON, stdout and stderr; arbitrary files or external telemetry require separate policy inspection. Source/provider SDK behavior, cloud WORM, production availability, RPO/RTO and real identity permissions are unassessed. Build/runtime verification and CODE.5 must run separately on candidate source. Security or policy failures cannot be offset by functional scores. A malformed candidate response fails its check; unavailable local execution resources are recorded as inconclusive.
