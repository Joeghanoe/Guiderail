---
type: Case
title: "C-NNN Return early instead of nesting if/else, and keep ternaries out of anything that reads as logic"
description: Control flow reads top to bottom when guard clauses return early; nested if/else and chained or branching ternaries hide which path is the normal one.
case_id: C-NNN
rule: /rules/code/code-3-names-say-what-it-is-for.md
verdict: open
status: draft
tags: [code, readability, control-flow, guard-clauses, ternary]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-25T06:14:20Z }
sources:
  - id: origin
    resource: direct feedback from the repo owner while reviewing a validator, a service and endpoint handlers ("no or minimal ternaries, they are hard to read, and return early; I see a lot of if-else nesting")
---

# Situation

No rule in `/rules/code/` covers the shape of control flow. Generated and hand-written code alike drifts into
three habits that the repo owner asks to avoid in every TeamValue repo: a normal path buried inside nested
`if`/`else` blocks, `else` branches after a `return` or `throw`, and ternaries that choose between two
non-trivial expressions or that are nested or chained.[^origin]

This case proposes a new rule next to CODE.3 (readability of what the code says), for example "CODE.8
Control flow returns early; ternaries stay trivial". `rule:` points at CODE.3 only because the case file needs an
existing rule to hang on.

# Why (open)

Early returns put the failure and edge cases first and leave the normal path at the left margin, so a reader
meets the happy path once, unindented. A ternary is fine when it picks a value that is obvious at a glance;
once it carries a call, a new object, a second condition or a message, an `if` with a `return` says the same
thing in a form that can be stepped through and put a breakpoint on.

Proposed rule text:

- Check the failing or special case first and return (or throw, or `continue`). Do not write `else` after a
  branch that returns, throws or continues.
- More than two levels of `if`/`else` nesting is a reason to extract a method or to invert conditions.
- A ternary is allowed for a short, side-effect-free choice between two simple values (for example a label).
  Do not nest or chain ternaries, and do not use one to choose between calls or to build results. Use `if`
  with an early return, a `switch` expression, or a small named method.

Reviewer note: this is a readability rule, so it is a `minor` finding unless the nesting hides a defect.

# Compliant pattern

## Good example

```csharp
public static IResult Commit(ImportOutcome outcome)
{
    if (outcome.Errors.Count > 0)
    {
        return Reject(outcome.Errors);
    }

    if (outcome.Result is null)
    {
        return NotFound();
    }

    return Created(outcome.Result);
}
```

## Bad example

```csharp
public static IResult Commit(ImportOutcome outcome)
{
    if (outcome.Errors.Count == 0)
    {
        if (outcome.Result is not null)
        {
            return Created(outcome.Result);
        }
        else
        {
            return NotFound();
        }
    }
    else
    {
        return Reject(outcome.Errors);
    }
}

// a ternary that chooses between two calls, with the condition hiding in the middle
return outcome.File is null ? BadRequest(outcome.Errors) : Ok(await service.Preview(outcome.File));
```

# Not verified

No analyzer or lint rule was identified that enforces this in C# or TypeScript. A reviewer rule is possible; a
gate is not obviously available (CA1822-style analyzers do not cover it). The "two levels" threshold is a
suggestion for the owner to confirm.

[^origin]: repo owner feedback, 2026-10-25
