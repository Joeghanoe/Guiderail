---
type: Example
title: "E-041 Return early and avoid nested conditional expressions"
description: Return early and avoid nested conditional expressions.
example_id: E-041
rule: /rules/code/code-11-return-early.md
verdict: violation
status: stable
verified: { by: human:teamvaluegroup, at: 2026-11-01T19:18:40Z }
tags: [feedback, regression]
generated: { by: codex/unknown, at: 2026-11-01T20:00:00Z }
example_file: src/ImportStatus.cs
---

# Situation

Guard clauses make exit conditions visible. Do not add else after a terminating branch. A short side-effect-free choice between simple values can stay a ternary; nested or chained ternaries and branching between operations should use explicit branches. This is a minor readability finding, not an invented correctness defect.

## Good example

```csharp
public static string ImportStatus(ImportOutcome outcome)
{
    if (outcome.HasErrors)
        return "Rejected";
    if (outcome.IsMissing)
        return "Missing";
    return "Created";
}
```

## Bad example

```csharp
public static string ImportStatus(ImportOutcome outcome)
{
    if (!outcome.HasErrors)
    {
        if (!outcome.IsMissing)
        {
            return "Created";
        }
        else
        {
            return "Missing";
        }
    }
    else
    {
        return "Rejected";
    }
}
```

# Evidence and limits

Prepared from the owner's feedback queue on 2026-11-01. Source snippets use neutral names. Model evaluation tests reviewer behavior, not execution of these snippets. The owner approved this example in the processing session on 2026-11-01. Approval concerns the expected reviewer behavior, not execution of the snippet.
