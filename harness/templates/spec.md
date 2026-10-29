---
type: Spec
title: "{{title}}"
description: <one sentence: what is different for the user when this is done>
spec_id: {{slug}}          # the stable id a scenario, a PR and a finding can all name (T.5)
status: draft              # draft | agreed | built | verified | dropped
work_item: {{work_item}}   # the tracker id, or `none - <the question the user answered>`
owner: {{owner}}           # who decides what done means
created: {{date}}
tags: [{{tags}}]
related:
  - "[[{{source_note}}]]"  # the incident, change or analysis note this spec came from
---

# Problem

What is wrong or missing now, in the words of the person who asked.[^requirement] One paragraph, no solution.

# Done means

One sentence. When the work item does not say it, this line is the user's answer to your question, quoted.
Never your own invention.

# Scope

- **In:** the one underlying problem this spec solves (DEL.3).
- **Out:** what someone will read into this and it does not cover.

# Acceptance criteria

| # | Criterion | Checked by | Evidence |
|---|---|---|---|
| A1 | <observable behaviour, in business terms> | <scenario tag `@{{slug}}-a1` (T.5), or the command that runs> | <what the change will show (DEL.3)> |

A criterion nobody can run is an open question, not a criterion. Behaviour the integration suite can reach
needs a scenario, not a promise (T.5); behaviour it cannot reach names the unit or contract test and why.

# Work packages

Only when this spec feeds `~/.harness/playbooks/orchestrate-workload.md`: one row per work package, each
with its file paths, the criteria it must satisfy, and the verification command that must pass.

| Package | Files | Criteria | Verification |
|---|---|---|---|

# Open questions

- <question> - <who answers> - blocks: <A1>

# Decisions not made here

Design choices this spec leaves open. Each is a candidate ADR, decided with Vegviser's `vegviser-adr` skill
and recorded in Vegviser, not here.

[^requirement]: <where the requirement came from: work item, [[note]], or the user's answer on {{date}}>
