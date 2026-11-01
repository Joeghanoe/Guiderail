---
type: Example
title: "E-048 Ternaries choose simple values rather than nested operations"
description: Ternaries choose simple values rather than nested operations.
example_id: E-048
rule: /rules/code/code-11-return-early.md
verdict: violation
status: stable
verified: { by: human:joeghanoe, at: 2026-11-01T19:18:40Z }
tags: [feedback, regression]
generated: { by: codex/unknown, at: 2026-11-01T20:00:00Z }
example_file: src/ImportStatus.cs
---

# Situation

A short pure label choice is allowed, as is a switch statement or switch expression when it makes the alternatives clear. A nested conditional expression hides the branches between operations. Report CODE.11 as readability, not a correctness failure.

## Good example

```csharp
public static string State(bool missing) => missing ? "Missing" : "Ready";
```

```csharp
public static string State(bool missing) => missing switch
{
    true => "Missing",
    false => "Ready"
};
```

## Bad example

```csharp
public static IResult Commit(ImportOutcome outcome)
{
    return outcome.HasErrors
        ? Reject(outcome.Errors)
        : outcome.IsMissing
            ? NotFound()
            : Created(outcome.Result);
}
```

# Evidence and limits

Prepared from the owner's feedback queue on 2026-11-01. Source snippets use neutral names. Model evaluation tests reviewer behavior, not execution of these snippets. The owner approved this example in the processing session on 2026-11-01. Approval concerns the expected reviewer behavior, not execution of the snippet.
