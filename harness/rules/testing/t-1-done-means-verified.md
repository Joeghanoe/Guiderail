---
type: Rule
title: "T.1 Done means verified: CI is the full gate, the project verify is the quick local subset"
description: CI runs the full gate; a quick project verify kept outside the repo runs the fast subset; new behaviour ships with a test; work is done only when it passes or every skipped step is named.
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

- CI is the authority: the PR pipeline runs the full gate. The agent's quick local check is the project verify, kept in `~/.golden-path-harness/projects/<repo-id>/verify.sh` (`tools/code/project-verify.sh path`), so the repo gets no second pipeline. A check CI misses is added to the project verify; a critical one is proposed to the repo's CI as a diff for a human ([CLD.2](../cloud/cld-2-humans-take-irreversible-actions.md)). A `scripts/verify.sh` committed in a repo is not used by the Stop hook.
- The full gate runs, in order: formatter in check mode, analyzers with warnings as errors, build, tests. The project verify's `--fast` is for the Stop hook and must take seconds: an incremental build and the unit tests, no restore, no format check, no integration tests.
- **Behavior over implementation:** Tests must verify observable outcomes, business rules, and critical invariants, not internal implementation details or mock call counts (`Verify(Times.Once)`). A good test fails when the behavior it protects breaks, and continues passing when the implementation is refactored without changing behavior.
- **Behavioral confidence over coverage:** High code coverage is not quality; tests must never exist solely to satisfy coverage numbers. Focus on meaningful decision paths, boundary cases, and failure conditions.
- **No unnecessary mocks:** Avoid mocking everything indiscriminately. Test coherent pieces of behavior with real lightweight collaborators where practical, isolating only external I/O, network, or clock boundaries.
- New behaviour ships with a test that calls it, even where neighbouring code has none. With no test project in reach, add the test file beside the code.
- Fix new warnings and lint issues in the code. A suppression is scoped to one line, names the rule and says why. No file- or repo-wide disables, no lowered thresholds.
- Check static-analysis findings before reporting done when the change touches code Sonar analyses. Read the IDE diagnostics for the changed files first (cheapest), then `tools/sonar/sonar-read.sh issues/search` with `impactSoftwareQualities=RELIABILITY,SECURITY`; a `types=BUG,VULNERABILITY` filter misses Reliability findings filed as code smells ([E-016](../../examples/e-016-sonar-findings-through-a-read-wrapper.md)).
- Report honestly: what ran, what failed (with output), what was skipped and why.

# Enforcement

[stop-verify.sh](../../hooks/stop-verify.sh) runs the project verify with `--fast` when an agent wants to stop and sends it back to work when it fails. The pipeline runs the full gate and blocks the PR.

# Related guidance

This rule applies [P6 Automation by Default](../../principles/p-06-automation-by-default.md).

Worked examples:

- [E-051 CI is the full gate; the quick verify lives outside the repo](../../examples/e-051-ci-is-the-gate-the-project-verify-is-the-quick-copy.md) (boundary).
