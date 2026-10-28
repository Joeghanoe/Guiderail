---
type: Rule
title: "CODE.6 Use what the platform already does before writing it again"
description: A check, validation or policy the platform provides is configured, not re-implemented; the reason to add your own is written next to it.
rule_id: CODE.6
principle: /principles/p-05-reuse-before-reinvention.md
tags: [code, iac, design]
applies_to: ["**/*.cs", "**/*.bicep", "**/*.xml", "**/*.yml"]
enforced_by: [review]
severity: major
status: stable
verified: { by: human:joeghanoe, at: 2026-10-18T18:52:51Z }
sources:
  - id: origin
    resource: recurring pull request review feedback, 2023-2026, one platform team
---

# Rule

- Before you add a check, ask what the platform already enforces. An API gateway validates subscription keys
  and request schemas; a message broker enforces its own authorization; a framework validates its options.
- Validate at the front door, with the platform's own mechanism, and only once. Do not repeat the check in
  every operation's policy or handler.
- Dead configuration (a product nobody subscribes to, a role the identity never uses) is removed (CODE.1).
- When you do add your own, a comment says what the platform does not cover. "The platform returns 500 and
  we need a 4xx" is a reason; "to be sure" is not.

# Boundary

Defence in depth is allowed where the cost of a missed check is high and the second check is cheap. The
comment says so.
