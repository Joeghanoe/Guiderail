---
type: Case
title: "C-009 A boolean flag that switches behaviour is named for the behaviour, or removed"
description: A parameter called isManual changes what a method does in several places; name the behaviour, pass the state explicitly, and drop parameters that make the method a no-op.
case_id: C-009
rule: /rules/code/code-3-names-say-what-it-is-for.md
verdict: violation
status: stable
verified: { by: human:joeghanoe, at: 2026-10-27T20:07:13Z }
tags: [naming, design]
example_file: src/OrderHandler.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T21:00:00Z }
sources:
  - id: evidence
    resource: pull request review threads on flag parameters and method naming (mined 2026-10-18)
---

# Situation

One method serves two callers: a queue trigger and a manual HTTP call. A flag tells the method which one
called it, and the method skips or changes steps based on the flag.

# Why (verdict)

`isManual` describes who called, not what should happen, so the logic is implicit: the reader has to find
every `if (!isManual)` to learn what the manual path does differently. A parameter that makes the method do
nothing when it is `false` is not a parameter at all; the caller should decide whether to call. The delivery
count is state of the caller, so it is passed in explicitly. Name the behaviour (`deadLetterOnError`) and the
reader sees what is different without reading the body (CODE.3).

# Compliant pattern

## Good example

```csharp
public sealed class OrderHandler(IOrderStore store, IMessageActions messages)
{
    public async Task HandleAsync(Order order, int deliveryCount, bool deadLetterOnError, CancellationToken ct)
    {
        try
        {
            await store.SaveAsync(order, ct);
        }
        catch (StoreUnavailableException) when (deadLetterOnError && deliveryCount >= 5)
        {
            await messages.DeadLetterAsync(order.Id, ct);
            throw;
        }
    }
}
```

The queue trigger calls it with `deadLetterOnError: true` and the delivery count from the message; the manual
endpoint calls it with `deadLetterOnError: false` and `deliveryCount: 1`.

## Bad example

```csharp
public sealed class OrderHandler(IOrderStore store, IMessageActions messages)
{
    public async Task HandleAsync(Order order, bool isManual, CancellationToken ct)
    {
        try
        {
            await store.SaveAsync(order, ct);
        }
        catch (StoreUnavailableException)
        {
            if (!isManual)
            {
                await messages.DeadLetterAsync(order.Id, ct);
            }

            throw;
        }
    }

    public async Task NotifyAsync(Order order, bool isManual, CancellationToken ct)
    {
        if (!isManual)       // when this is false, the method does nothing at all
        {
            await store.MarkNotifiedAsync(order.Id, ct);
        }
    }
}
```

# Not verified

Written for this example in neutral names.
