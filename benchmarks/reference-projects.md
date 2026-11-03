# Reference project validation workflow

Use existing projects as a validation set for the harness. Projects may contain known defects, accepted deviations and good implementations. Record which is which so an evaluation can measure whether the harness finds the gaps, proposes appropriate improvements and preserves correct behavior. A reference project is evidence, not an assertion that its implementation is the standard.

This workflow follows [ADR 0005](../docs/adr/0005-evaluation-and-continuous-improvement.md) and the [case separation policy](cases/README.md). The local project registry described here is a manual convention, not a new runner API.

## 1. Choose the evaluation role

Assign each component one role before documenting its findings.

| Role | Use | Boundary |
| --- | --- | --- |
| Training | Derive rules, templates and examples | May teach the harness; cannot also count as independent validation |
| Validation | Compare harness revisions against fixed expectations | Keep findings out of candidate context; do not turn these components into examples or tailor rules to their findings |
| Holdout | Release evaluation on material unseen during tuning | Keep sealed outside the registry and follow the existing holdout policy |

Validation scores can guide the choice between independently proposed harness changes. If a component becomes material for directly teaching the harness, record its reassignment to training and replace its validation coverage with an unseen component. Do not keep reporting it as independent validation.

## 2. Register a local project

Keep project sources and private annotations outside this repository, under the configured harness home:

```text
$GOLDEN_PATH_HOME/testing/
  reference-projects/
    project-01/
      project                  symlink to a checkout, or a copied project directory
      reference.json           private registration and source pin
      findings.md              private evaluation expectations
      snapshots/
        baseline-01/           frozen source files for this baseline
  runs/                        separate workspaces, traces, diffs and reports per run
```

`GOLDEN_PATH_HOME` defaults to `~/.golden-path-harness`. Use neutral project IDs. Keep real names and local source paths in private registration files; version only neutral benchmark definitions in `benchmarks/`.

For convenient access to a checkout, create a symlink:

```bash
reference_root="${GOLDEN_PATH_HOME:-$HOME/.golden-path-harness}/testing/reference-projects"
project_dir="$reference_root/project-01"
mkdir -p "$project_dir/snapshots"
ln -s /absolute/path/to/project "$project_dir/project"
```

Alternatively, create `project/` and copy the required source files into it. Copying makes the registration independent of the original checkout but requires an explicit refresh. A symlink follows changes in the checkout. Neither is a frozen benchmark baseline by itself.

Create `reference.json` using this example as a manual template. Replace placeholders and command examples with the project's actual values:

```json
{
  "id": "project-01",
  "role": "validation",
  "owner": "human:<reviewer>",
  "source_path": "/absolute/path/to/project",
  "baseline_id": "baseline-01",
  "source_revision": "<full Git commit SHA, or null for a source without Git>",
  "snapshot_path": "snapshots/baseline-01",
  "snapshot_manifest": "<path to the file list and SHA-256 hashes>",
  "scope": "<components and excluded files>",
  "commands": {
    "build": "<build command>",
    "test": "<test command>"
  },
  "prerequisites": ["<SDK, local dependencies and required test services>"],
  "baseline_checks": "<path to build/test results and known failures>",
  "reviewed_at": "<UTC timestamp>"
}
```

## 3. Freeze the starting state

Create a new snapshot directory for each baseline. Never update a baseline in place after using it for a comparison.

For a Git project, first confirm the source tree is clean and record its full commit SHA:

```bash
git -C "$project_dir/project" status --short
git -C "$project_dir/project" rev-parse HEAD
```

Copy the selected files from that revision into the snapshot and record each relative path and SHA-256 hash. For a project without Git, the file list and hashes define the source pin. Record any exclusions and include the files needed to interpret the task. Exclude credentials, local environment files and generated build output. Check symlinks in the copied sources so a snapshot cannot silently depend on a changing external file.

Run the applicable build and tests against the baseline and save their outcomes. Record missing prerequisites and inherited failures. A partial snapshot may not build; report that limitation rather than treating it as a candidate failure.

## 4. Record expected findings and preserved behavior

Write `findings.md` against the frozen baseline. Give each expectation a stable ID. Use this table as a template and replace the illustrative entries:

| ID | Classification | Location and evidence | Applicable rule | Expected outcome | Verification |
| --- | --- | --- | --- | --- | --- |
| F01 | Known gap | File, symbol and observed failure | Existing rule ID, or an explicitly unresolved standards question | Detect the problem; for a remediation task, correct the behavior within scope | Independent assertion or human rubric |
| F02 | Accepted deviation | File, context and named human decision | Rule and reason for exception | Preserve the approved exception | Review the rationale and resulting diff |
| F03 | Correct behavior | File and evidence of the existing behavior | Applicable rule | Preserve it and avoid a false-positive finding | Regression check |

For each entry, record the impact, scope, reviewer and evidence needed to decide pass, fail or inconclusive. State acceptable alternative implementations where relevant. Freeze these expectations before running the candidate. An agent's initial audit can suggest findings, but a human must validate them before they become evaluation expectations.

Known findings are not necessarily exhaustive. Have a human adjudicate additional findings before calling them false positives. Record ambiguous standards as unresolved rather than silently treating project preferences as harness rules.

## 5. Define an audit or change task

An audit task asks the candidate to identify relevant problems. Grade detection of known gaps, false positives and recognition of accepted deviations. A change task asks for a scoped improvement. Grade the requested behavior, introduced regressions and preservation of the recorded correct behavior. Do not require a scoped change to fix every inherited defect.

Keep `task.md` separate from evaluator expectations. The candidate receives only the task, selected source snapshot and harness instructions. The evaluator receives the private findings and acceptance checks. Keeping files outside the workspace prevents accidental prompt inclusion but does not enforce isolation against an agent with broader filesystem access; report the actual execution boundary.

For executable brownfield cases, use the existing [case format and commands](cases/README.md):

- Version `task.md`, hidden `criteria.md`, `case.json` and `snapshot.json` under `benchmarks/cases/validation/<case-id>/`, using neutral aliases.
- Keep real source mappings in `~/.harness-evaluation/private/`. Point them at the frozen snapshot, not the live checkout. Follow an existing case and the mapping contract in `harness/tools/testing/run_brownfield.py`.
- The runner currently uses that fixed private directory; it does not discover `reference.json` or follow `GOLDEN_PATH_HOME` for source mappings. Its snapshot file hashes must match the mapped sources.
- The runner executes scoped change tasks on partial snapshots. Whole-project audits remain a manual evaluation under this workflow; do not assume that registering a project enables automated audit or full-project build verification.

## 6. Run and compare

Give every run a fresh writable copy of the frozen sources. Never run remediation against the registered checkout or frozen snapshot. Keep candidate workspaces separate from evaluator files.

Save results under `$GOLDEN_PATH_HOME/testing/runs/<run-id>/`. Record the baseline and case versions, harness commit, evaluator version, model, adapter, options, execution boundary and prerequisites. Preserve the prompt, trace, diff, verification output, runtime and usage evidence. Record unavailable measurements as unknown.

Compare harness revisions on the same frozen baseline, task and evaluator expectations, with equivalent execution conditions. Repeat model runs when feasible. Report missed known gaps, adjudicated false positives, successful improvements, inherited failures and introduced regressions separately. Follow the existing benchmark scoring policy when producing a benchmark score; this workflow adds no new threshold.

If the expected result and agent output disagree, classify the cause before changing anything: project defect, evaluator defect, incomplete principle or exception, model/harness failure, or insufficient evidence. For supported brownfield runs, use the [diagnosis commands](cases/README.md#diagnosing-a-run). Never edit expectations during a run to make the candidate pass. Version reviewed evaluator corrections and regrade saved evidence where supported.

## 7. Add or refresh a project later

For each additional project, repeat registration, role assignment, source freezing and human review of expectations. When source code or expectations change, create a new baseline or case version and keep the old one with its run evidence. Recheck accepted deviations against the applicable standards version. Compare runs only when their recorded inputs and conditions support the comparison.

Before the first run, confirm that the project has an owner and role, a reproducible source pin, reviewed expectations, baseline verification results, a scoped task and a separate candidate workspace.
