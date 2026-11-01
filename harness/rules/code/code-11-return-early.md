---
type: Rule
title: "CODE.11 Return early and keep conditional expressions simple"
description: Prefer guard clauses to nested branches, omit else after a terminating branch, and reserve ternaries for short side-effect-free value choices.
rule_id: CODE.11
principle: /principles/p-11-standards-enable-innovation.md
tags: [code, readability, control-flow]
applies_to: ["**/*.cs", "**/*.ts", "**/*.tsx", "**/*.js"]
enforced_by: [review]
severity: minor
status: draft
sources:
  - id: origin
    resource: owner feedback on early returns and ternaries, processed into E-041 on 2026-11-01
---

# Rule

Use guard clauses when they remove nesting. A branch that returns, throws or continues does not need an else branch afterward. Keep the normal path easy to follow.

A ternary may choose between two simple, side-effect-free values. Do not nest or chain ternaries, or use them to choose between operations. Use explicit branches, a switch expression or a small method when that makes the choices clearer.

This is a minor readability finding unless evidence establishes a separate defect. Do not invent a mandatory nesting-depth threshold or require extraction of every conditional.

# Boundary

An if/else that makes two non-terminating alternatives clear can stay. A short label choice such as `missing ? "Missing" : "Ready"` can stay.
