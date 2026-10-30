---
type: Rule
title: "H.2 Repeated work moves up the automation ladder"
description: A task done a second time becomes a playbook; a playbook that is mostly commands becomes a script; a script that guards a rule becomes a hook or CI check.
rule_id: H.2
principle: [/principles/p-06-automation-by-default.md, /principles/p-12-continuous-improvement.md]
tags: [harness, automation]
applies_to: ["**"]
enforced_by: [instructions, review]
severity: minor
status: stable
---

# Rule

```
one-off command  ->  playbook (concept)  ->  script in tools/  ->  hook or CI check
```

- The second time an agent does the same task, it proposes a playbook as an example with
  `verdict: automation-candidate`.
- A playbook that is mostly commands becomes a script: parameters as arguments, sorted output, a header with
  purpose, input, output and an example.
- A review finding that keeps being accepted (`fixed` on the PR thread) is a candidate to become an analyzer,
  an architecture test or a check script. The rule's `enforced_by` then names the tool.

Each step up costs fewer tokens and gives the same answer every run. Look in `tools/` and `playbooks/`
before writing a second variant of something that exists.
