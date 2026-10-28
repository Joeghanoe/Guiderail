---
type: Case
title: "C-NNN <what happened, in words someone would search for>"
description: <one sentence>
case_id: C-NNN
rule: /rules/<area>/<rule-file>.md
verdict: violation        # violation | compliant | boundary | rejected | open | automation-candidate
status: draft             # a human sets stable, and adds verified
tags: []
owner: <human:id>          # boundary only: who accepted the deviation
stale_after: <yyyy-mm-ddT00:00:00Z>   # boundary only: when the deviation must be reviewed again
example_file: <src/Program.cs>   # optional: the file the examples live in, when the rule depends on it
generated: { by: <agent>/<model>, at: <yyyy-mm-ddThh:mm:ssZ> }
sources:                   # optional internal provenance; the case itself names no project
  - id: evidence
    resource: <repo>@<commit>:<path>#L<from>-L<to>
  - id: requirement        # boundary only: the requirement or exception record that allows the deviation
    resource: <the kind of requirement, e.g. "a contract clause requiring one interface per customer">
---

# Situation

What the code or config does, in neutral names that fit any repo.[^evidence]

# Why (verdict)

How the rule and its principle apply. For `boundary`: when the rule does not apply. For `rejected`: which
principle or hard rule the feedback contradicts.

# Compliant pattern

Optional: what good looks like, with a source.

## Good example

```<language>
<code snippet>
```

## Bad example

```<language>
<code snippet>
```

# Optional reviewer behavior evaluation

Use only when the case defines a reviewer behavior scenario in addition to its code examples.
`eval_behavior: adversarial` feeds `## PR description` to the reviewer as untrusted data.
`eval_behavior: rename` uses `eval_before_file` and `eval_after_file` to evaluate a pure file rename.
`eval_critical: true` requires every configured repeat to pass. Evaluation cases are held out from
the reviewer's context while testing; `boundary` cases remain visible.

## PR description

<untrusted PR description text>

## Before example

```<language>
<same source content used by the after example>
```

`eval_before_file` and `eval_after_file` are required for rename evaluations. The runner also needs the
`## Good example` block as the identical source content on both sides of the rename.

# Not verified

What you could not check.

[^evidence]: <short label>
