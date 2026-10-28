---
type: Rule
title: "T.5 Behaviour the integration suite can reach comes with a scenario"
description: If a repo has integration or E2E tests, a change in behaviour adds or updates a scenario that states that intent.
rule_id: T.5
principle: [/principles/p-01-business-before-technology.md, /principles/p-08-observable-by-design.md]
tags: [testing, integration, e2e, bdd]
applies_to: ["**"]
enforced_by: [gate:/gates/scenario-presence.md, review]
severity: major
status: stable
---

# Rule

A change that alters behaviour reachable through the suite's entry points (APIM, an HTTP trigger, a worker's
`/invoke`, a portal journey) adds or updates at least one scenario that describes the behaviour in business
terms. Scenario first, code second: the scenario is the acceptance criterion of the work item.

Scenarios carry a stable intent ID or tag (`DS-4`, `@b2b-external`) so a test, a PR and a finding can name the
same behaviour.

# Two checks

1. Presence, deterministic: `tools/testing/check-scenarios.py` maps changed components to their scenario folders
   (`.harness-scenarios.json` in the repo). A changed component needs a changed scenario, or a PR description
   line `e2e: n/a - <reason>`.
2. Fit, review: does the scenario cover the intent of the change, not just something in the same folder?

# Boundary

- A refactor without a change in behaviour: `e2e: n/a - refactor`, and the existing scenarios stay green.
- Behaviour the suite cannot reach (a partner's system without a test environment): a unit or contract test,
  and the PR says why.
- Infrastructure-only changes are covered by the post-deploy smoke step, not by a new scenario.
