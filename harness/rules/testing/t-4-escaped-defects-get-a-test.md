---
type: Rule
title: "T.4 A defect found in DEV or production gets a test in layer 0 or 1"
description: Every bug that a later layer finds is reproduced by a local or PR test in the fix.
rule_id: T.4
principle: /principles/p-12-continuous-improvement.md
tags: [testing, defects]
applies_to: ["**"]
enforced_by: [review]
severity: major
status: stable
---

# Rule

When layer 2 or 3 finds a defect, the fix includes a test in layer 0 or 1 that fails without the fix. If that is impossible (the defect lives in a third party, or only in the environment), the PR says why, and the cause becomes a known issue in the repo.

# Related guidance

This rule applies [P12 Continuous Improvement](../../principles/p-12-continuous-improvement.md).
