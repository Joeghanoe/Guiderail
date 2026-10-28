---
type: Rule
title: "H.1 Feedback becomes a case; principles change only by a human decision"
description: A correction of output that came from the harness is recorded as a proposed case, not as an edited rule.
rule_id: H.1
principle: [/principles/p-03-governed-autonomy.md, /principles/p-12-continuous-improvement.md]
tags: [harness, feedback]
applies_to: ["**"]
enforced_by: [instructions, playbook:process-feedback]
severity: major
status: stable
---

# Rule

When a user corrects output that came from a rule (a wrong finding, a missed issue, a rule that does not fit),
the agent writes a case following `/templates/case.md` into `~/.harness-feedback/`, with
`status: draft` and no `verified` key, and goes on with the task. It does not edit rules or principles.

| Level | Who changes it | How |
|---|---|---|
| Principles | Vegviser's owner | Vegviser's own process; the harness only points to P1-P13 |
| Rules | A human | A PR on the harness repo that cites the cases behind it |
| Cases | An agent proposes, a human accepts | The human adds `verified: { by: human:<id>, at: ... }` |

The harness defends its rules: when feedback contradicts a principle or a hard rule, the agent says so,
cites it, and records the case with `verdict: rejected` and the reason, so the same objection is not raised
again. It does not argue for the sake of it: when the case shows the rule does not fit, the proposal is a
boundary case, not a removal.

See [process-feedback](/playbooks/process-feedback.md).
