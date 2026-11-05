---
type: Rule
title: "H.1 Feedback becomes an example; principles change only by a human decision"
description: A correction of output that came from the harness is recorded as a proposed example, not as an edited rule.
rule_id: H.1
principle: [/principles/p-03-governed-autonomy.md, /principles/p-12-continuous-improvement.md]
tags: [harness, feedback]
applies_to: ["**"]
enforced_by: [instructions, playbook:process-feedback]
severity: major
status: stable
---

# Rule

When a user corrects output that came from a rule (a wrong finding, a missed issue, a rule that does not fit), the agent captures a draft and goes on with the task. It does not edit rules or principles. [Process feedback](/playbooks/process-feedback.md) defines capture, classification and submission.

| Level | Who changes it | How |
| --- | --- | --- |
| Principles | Vegviser's owner | Vegviser's own process; the harness only points to P1-P13 |
| Rules | A human | A PR on the harness repo that cites the examples behind it |
| Examples | An agent proposes, a human accepts | The human adds `verified: { by: human:<id>, at: ... }` |

Feedback cannot override a principle, hard rule or human-reviewed precedent. The playbook defines how to record contradictions and legitimate boundaries without silently changing that authority.

# Related guidance

This rule applies [P3 Governed Autonomy](../../principles/p-03-governed-autonomy.md), [P12 Continuous Improvement](../../principles/p-12-continuous-improvement.md).
