---
type: Rule
title: "CODE.3 Names and parameters say what they are for, and flags do not hide logic"
description: A name states the purpose; a boolean parameter that switches behaviour is split or named for the behaviour; a parameter that does nothing when false does not exist.
rule_id: CODE.3
principle: /principles/p-11-standards-enable-innovation.md
tags: [code, naming]
applies_to: ["**/*.cs"]
enforced_by: [review]
severity: minor
status: stable
verified: { by: human:joeghanoe, at: 2026-10-18T18:52:51Z }
sources:
  - id: origin
    resource: recurring pull request review feedback, 2023-2026, one platform team
---

# Rule

- A class, method or parameter is named for what it does or is for, in the words of the domain: a health
  check for the service is `Health`, not named after one of its dependencies; a method that is called from
  a trigger is not named `HandleMessage` when it creates a user.
- A boolean parameter that makes a method behave in two ways hides logic. Name it for the behaviour it
  causes (`deadLetterOnError`), or make two methods. A behavior-named flag such as `deadLetterOnError` is
  already the compliant pattern; do not flag it just because it selects behavior.
- A parameter that makes the method do nothing when it is `false` is removed; the caller decides whether to
  call.
- State a method needs (a delivery count, a mode) is passed in explicitly, not inferred from where the
  method is called.
- A name in code follows the vocabulary the product uses outside the code.

# Boundary

A name imposed by a framework or a public contract stays as it is; wrap it in a clearer name inside.
