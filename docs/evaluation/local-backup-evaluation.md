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

## Coverage limits

Retention is an eligibility simulation, not deletion or immutability enforcement. SQL data is a pre-exported
artifact, not a live database. Operational output inspected by F10 consists of response JSON, stdout and
stderr; arbitrary files or external telemetry require separate policy inspection. Source/provider SDK
behavior, cloud WORM, production availability, RPO/RTO and real identity permissions are unassessed.
Build/runtime verification and CODE.5 must run separately on candidate source. Security or policy failures
cannot be offset by functional scores. A malformed candidate response fails its check; unavailable local
execution resources are recorded as inconclusive.
