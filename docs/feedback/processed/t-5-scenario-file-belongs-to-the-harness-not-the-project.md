---
type: Example
title: "C-NNN A project repo is not asked for a scenario config file just to feed a harness gate"
description: A review raised "no .harness-scenarios.json" as a finding on a project that has a working integration suite; the owner holds that harness machinery stays in the harness, not in every repo.
example_id: C-NNN
rule: /rules/testing/t-5-behaviour-has-a-scenario.md
verdict: boundary
status: processed
tags: [testing, scenarios, consumer-repos]
owner: human:joeghanoe
stale_after: 2027-05-01T00:00:00Z
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-11-01T18:00:00Z }
sources:
  - id: requirement
    resource: the repo owner's decision that gate configuration files are the harness's concern and are not forced on project repos
---

# Situation

A project has an integration suite whose tests are named after the behaviour they check and run in CI. A review finding asked the project to add `.harness-scenarios.json`, intent traits on every test and a CI step for `check-scenarios.py`, because the scenario-presence gate cannot run without them.

# Why (boundary)

T.5 asks that a change in behaviour adds or updates a test that states its intent. It does not ask a project to carry the gate's own configuration. Where the project's tests already state intent by name and run in CI, the missing config file is a gap in the gate's reach, not in the project, and the finding is not raised. The rule stays: a behaviour change with no test that states it is still a finding.

# Compliant pattern

The gate infers its components from the repo (or the harness carries the mapping), so a project adopts nothing beyond its own tests.

## Good example

```text
No finding: behaviour changes arrive with tests named after the behaviour they check, and CI runs them.
```

## Bad example

```text
Finding T.5: no .harness-scenarios.json in the repo root.
```

# Disposition

Owner declined E-043 on 2026-11-01. Implemented as opt-in scaffolding/gate guidance and deterministic scaffold coverage instead; no reviewer eval example is required.
