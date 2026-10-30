---
type: Playbook
title: Start a new repo or service design-first
description: Turn a task for a new repo or service into a solution design, ADRs, the repo's own AGENTS.md and a verify command before feature code, then build in verified slices and report what matches the design.
tags: [greenfield, design, architecture, planning]
status: draft
---

# When

The repo has no source yet, or the task asks for a new service or application. Applies when the task says
"choose your architecture" too (DEL.4). Not for a change to an existing service: its own shape is the convention
([scaffold-from-conventions](scaffold-from-conventions.md)).

# Steps

1. **Scaffold.** `~/.golden-path-harness/harness/tools/greenfield/greenfield-init.sh --service` (omit `--service` for a repo that
   runs no operations) writes the design skeleton, the repo's `AGENTS.md`, `scripts/verify.sh`, `Directory.Build.props`
   and `BannedSymbols.txt`, and never overwrites. `scripts/verify.sh` runs the design gate
   (`tools/greenfield/design-check.py`) and the CODE.5 checker; it fails until the design is filled in and the code
   follows it.
2. **Load the rules, once.** Open `index.md`, then run the `select` command from the base instructions on the
   paths you expect to create. Open the rules it names; DEL.4, CODE.8, OBS.3, T.1 to T.5, SEC.2 and CODE.5 apply
   to almost every service. Name what you skipped.
3. **State what done means.** Quote the task's own requirements and acceptance criteria; they are the spec
   ([write-spec](write-spec.md)). Do not invent criteria. List ambiguities with the reading you took.
4. **Fill `docs/solution-design.md`.** Answer every heading. Decide
   these before code, because they are expensive to change after data exists: the stored layout, what one
   restore point or unit contains, the identity of a run and what repeating it does, the failure model, the
   reason codes, the events, the retention rule, what input is never trusted.
5. **One ADR per hard-to-reverse decision** in `docs/adr/` (DEL.4). Typical: stored layout, run identity and
   idempotency, failure semantics, retention, storage medium behind its interface.
6. **Fill the repo's `AGENTS.md`**: layout, vocabulary, current decisions,
   "follow a change across boundaries" with a **checked** or **documented** mark on each entry (CODE.7), verify,
   when to ask. Adapt `scripts/verify.sh` to the repo's toolchain without removing the gate steps.
7. **Build in slices** (orchestrate-workload): contracts and models; interfaces and the composition root; one
   implementation per kind; the operations; the entry point. Each slice compiles and has tests in its layer
   (T.3): unit tests per component against fakes, and scenario tests through the real entry point (T.5).
   Interfaces for sources, stores, clock and runners from the first slice (CODE.8). One type per file (CODE.5).
8. **Keep design and code one story.** When the code forces a different choice, change the design doc and the
   ADR in the same step. A design that no longer describes the code is a finding.
9. **Verify** with `scripts/verify.sh` (T.1), including the format check.
10. **Report** in `REPORT.md`: what matches the design, where the code diverges and why, rule IDs applied, rules
   consciously not applied, what was not verified. Do not claim a rule you did not check.

# Boundaries

A design is the content of the choice, not ceremony: short, specific, and true. Do not copy a design from a
neighbouring repo; read it for questions to answer, not for the answers.
