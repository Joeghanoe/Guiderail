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
