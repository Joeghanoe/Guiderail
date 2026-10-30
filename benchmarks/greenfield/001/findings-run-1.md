# greenfield-001, first run: what the harness lacked

Run `greenfield-001-rancher-smoke`, 2026-10-29, claude-sonnet-5-5, container isolation, exploratory. Harness
commit 686e1a8. Functional F01-F10 pass, build and tests pass, CODE.5 0 findings, 228 s, 67 tool calls.

## Conclusion

The candidate passed every check the benchmark had and delivered none of what the reference repository is built
around. The benchmark measured behaviour only; the harness had no rule that asked for a design, and the
agent never opened the harness (its trace shows `ls .harness | head`, then code). Both are harness gaps.

## Gap against the reference design, by rule

| Reference practice | Candidate | Harness rule that should have driven it | Gap |
|---|---|---|---|
| A solution design that opens with the one question and fixes layout, failure model, events, retention before code | none; `REPORT.md` written after | none (P2 only points at Vegviser) | no rule, no template: **DEL.4** added |
| ADR per hard-to-reverse decision (stored layout, run identity, retention) | none | write-spec routes to Vegviser, never triggered for greenfield | **DEL.4**, start-greenfield playbook |
| Repo `AGENTS.md`: layout, vocabulary, change map, verify | the base file only | `templates/repo/AGENTS.md` existed outside the bundle, invisible to installed agents and to the candidate | templates moved under `harness/`, **DEL.4** |
| `scripts/verify.sh` before code | absent; report says "does not exist, so not run" | T.1 says run it, nothing says create it | init script writes it, **T.1** unchanged |
| Interfaces for source, sink, clock, runner; one composition root; DI | `new FilesSourceBackup()` in a dictionary inside `BackupOperation`; storage written with `File.*` directly; no sink | T.2 bans constructions, nothing prescribes the shape | **CODE.8** added |
| Fixed event catalogue, error-code catalogue, status and health calls, no names or payload | per-source codes as string literals; no events, no status, no health | OBS.1 (health only) | **OBS.3** added |
| Tests per layer: unit per component plus scenarios | 10 tests, all through `Program.Main` in one file | T.3 and T.5 say the layers exist | design gate D09 |
| Layout `Models/ Services/ Services/Interface/ Helpers/` | `Operations/ Sources/ Restore/ Storage/ Infrastructure/` (reasonable, but no dependency direction stated) | CODE.5 only covers one type per file | **CODE.8** |

## Benchmark gaps (separate from the harness)

- The task is a thin slice of the reference: no status or health call, no dry run, no exclusions, no event
  contract, no hostile identifiers, no repeatable run identity. A candidate cannot show design quality on a
  task that never asks for the behaviour the design exists for. `greenfield-002` adds F11-F16.
- There was no dimension for design evidence. `design-check.py` now reports D01-D09 as a separate
  architecture dimension, calibrated on this run (9 of 9 fail) and on the reference repository (passes all but
  D04, because the reference has no `scripts/verify.sh`).
- 001 stays frozen as the baseline so runs remain comparable.

## Not a finding

Functionality, build and CODE.5 were good. The candidate's `REPORT.md` was honest (it said it could not run
`scripts/verify.sh` and had not tested against the evaluator).

## Improvement loop, 2026-10-30

All runs: claude-sonnet-5-5, container isolation, exploratory (policy and behavior stay inconclusive), same prompt.
"Design" is `design-check.py` (D01-D09, service profile) applied to the workspace afterwards. "Src before design" is the
number of C# files written before `docs/solution-design.md`, from the trace.

| Run | Harness | Benchmark | Functional | CODE.5 | Design | Src before design | What happened |
|---|---|---|---|---|---|---|---|
| 1 `rancher-smoke` | 686e1a8 | 001 | F01-F10 pass | 0 | 0/9 | n/a | never opened `.harness`; no design, ADR, repo AGENTS.md, verify.sh |
| 2 `r2-design-first` | + DEL.4, CODE.8, OBS.3, playbook, template | 001 | F01-F10 pass | 4 findings | 1/9 | 30 | read the base text only; 15-line design after the code; report says no rules were read |
| 3 `r3-design-gate` | + init script, design gate | 001 | not graded | 0 | 0/9 | n/a | stopped at 17 s: ran the init script, Claude Code asked for approval, headless cannot answer |
| 4 `r4-design-gate` | + allow rules | 001 | F01-F10 pass | 0 | 8/9 | 51 | script copied without exec bit and `bash` form not allowed, files recreated by hand; D03 failed because 001 installs the base text as `AGENTS.md` |
| 5 `002-r1` | + `bash` form, base in `AGENTS.base.md` | 002 | F01-F16 pass | 0 | 9/9 | 1 | ran the init script, design and 3 ADRs before the real code, `scripts/verify.sh` passes |

## Causes and fixes

| # | Gap | Cause | Fix | Evidence |
|---|---|---|---|---|
| 1 | No design, ADR, repo AGENTS.md | no rule asked for them | DEL.4, template, playbook | run 2 |
| 2 | Harness ignored | pointers to files are not followed; only an imperative first command was | `greenfield-init.sh`, gate in `verify.sh` | runs 2 vs 4 |
| 3 | Structure ignored (no interfaces, `new` collaborators, no events) | T.2 bans constructions but prescribes no shape | CODE.8, OBS.3, D05-D08 | run 1 vs 5 |
| 4 | Templates invisible to installed agents | they lived in `infra/` outside the bundle | moved to `harness/templates/repo` | run 1 |
| 5 | Scaffold command blocked | copy lost the exec bit; allow rules did not name the `bash` form | run through `bash`; allow rule in `install.sh` and the adapter | runs 3, 4 |
| 6 | Repo AGENTS.md could not exist | 001 installs the base text as `AGENTS.md` | 002 imports it from `AGENTS.base.md` | run 4 |
| 7 | Benchmark measured behaviour only | no status, health, dry run, exclusions, events, hostile ids; no design dimension | `greenfield-002` F11-F16, `design-check.py`, order evidence | run 5 |

## Open

- One sample per configuration. The loop shows the mechanism works; it does not show reliability. Repeat each
  configuration before comparing.
- `design-check.py` proves structure, not quality. A human reads run 5's design and ADRs against the reference.
- The init script and gate are now known to the candidate (it read `design-check.py`). Treat D01-D09 as the
  harness's own rules, not a hidden test; F01-F16 stay hidden.
- DEL.4, CODE.8, OBS.3, the playbook and the gate are `status: draft`; a human verifies them (H.1).
- The reference has no `scripts/verify.sh`, so it fails D04. Decide whether D04 stays.
