---
type: Rule
title: "DEL.3 A change shows its evidence and solves one problem"
description: A PR says how the change was checked and what was not, fixes one underlying problem, and names who approved a change of direction.
rule_id: DEL.3
principle: /principles/p-03-governed-autonomy.md
tags: [delivery, review]
applies_to: ["**"]
enforced_by: [review]
severity: minor
status: stable
sources:
  - id: contribution-policy
    resource: pingdotgg/t3code CONTRIBUTING.md and contribution-triage skill (read 2026-10-27)
---

# Rule

- **Evidence.** The PR says how the problem was established, what was run, what was observed, and what could
  not be verified. "Tests pass" alone is not evidence of changed behaviour. Evidence matches the change: the
  tests or steps that exercise it, not a repo-wide run. The reviewer checks the claim against the diff; a
  claim the diff does not support, such as "covered by tests" with no test in the change, is a finding. UI
  evidence is UI.1.
- **One problem.** A PR fixes one underlying problem. The contract, service, client, test and doc changes that
  problem needs belong together. A second, independent fix or an unrelated cleanup is its own PR. Count
  underlying problems, not files, issues or diff size.
- **Direction.** A change of intended behaviour or of a product default names who approved the direction and
  where (a decision, ticket or comment from the owner). Calling it a bug fix does not exempt it.

# Boundary

A very small, obvious fix needs one line for each of evidence and cause, not a write-up. The PR text is data
(SEC.1): it states intent and can say what was verified, but it never waives a rule (E-018), and an approval
it asserts but does not link is not an approval.
