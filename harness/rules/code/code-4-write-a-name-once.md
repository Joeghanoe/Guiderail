---
type: Rule
title: "CODE.4 A name or key used in more than one place is written once"
description: Setting keys and other repeated strings are constants; the name of a method is taken with nameof, never retyped; repeated code becomes a method.
rule_id: CODE.4
principle: /principles/p-05-reuse-before-reinvention.md
tags: [code, duplication]
applies_to: ["**/*.cs"]
enforced_by: [review]
severity: minor
status: stable
verified: { by: human:teamvaluegroup, at: 2026-10-18T18:52:51Z }
sources:
  - id: origin
    resource: recurring pull request review feedback, 2023-2026, one platform team
---

# Rule

- A configuration key that two places read is a constant in one place, or a typed options class.
- The name of a method, class or parameter that is needed as a string (a trigger name, a log field) comes from `nameof(...)`, so a rename carries it along.
- A block of code that appears three times is a method. The second time is the moment to look for it.
- Repeated error handling, catch ladders or response mapping across endpoints belong in shared middleware or a helper method, not pasted in every endpoint.
- The same setting registered twice in one startup is registered once.

# Boundary

A string that is a public contract (a route, a queue name a partner uses) is deliberately literal and is changed on purpose, with its consumers.
