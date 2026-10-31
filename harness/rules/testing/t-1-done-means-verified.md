---
type: Rule
title: "T.1 Done means verified, with the same command locally and in CI"
description: One verify command runs format, analyzers, build and tests; work is done only when it passes or every skipped step is named.
rule_id: T.1
principle: /principles/p-06-automation-by-default.md
tags: [testing, verification, ci]
applies_to: ["**"]
enforced_by: [hook:stop-verify, script:verify, review]
severity: blocker
status: stable
sources:
  - id: verification
    resource: skills/verification/verification/SKILL.md (AI Hub main b0cc2ae)
---

# Rule

- Every repo has one verify command (`scripts/verify.sh`). Local runs, the agent's Stop hook and the PR
  pipeline call the same command, so "green locally" means "green in CI".
- It runs, in order: formatter in check mode, analyzers with warnings as errors, build, tests.
  `--fast` is for the Stop hook and must take seconds: an incremental build and the unit tests, no
  restore, no format check, no integration tests. CI never passes `--fast`.
- New behaviour ships with a test that calls it, even where neighbouring code has none. With no test project in
  reach, add the test file beside the code.
- Fix new warnings and lint issues in the code. A suppression is scoped to one line, names the rule and
  says why. No file- or repo-wide disables, no lowered thresholds.
- Check static-analysis findings before reporting done when the change touches code Sonar analyses. Read the
  IDE diagnostics for the changed files first (cheapest), then `tools/sonar/sonar-read.sh issues/search` with
  `impactSoftwareQualities=RELIABILITY,SECURITY`; a `types=BUG,VULNERABILITY` filter misses Reliability
  findings filed as code smells (E-016).
- Report honestly: what ran, what failed (with output), what was skipped and why.

# Enforcement

`hooks/stop-verify.sh` runs `scripts/verify.sh --fast` when an agent wants to stop and sends it back to
work when it fails. The pipeline runs the full command and blocks the PR.
