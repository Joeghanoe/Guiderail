---
type: Example
title: "E-009 A boolean flag that switches behaviour is named for the behaviour, or removed"
description: Name boolean parameters after the concrete behavior they enable, or eliminate them in favor of explicit method calls.
example_id: E-009
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

A single method handles both queue messages and manual HTTP calls, using a generic `isManual` flag to toggle multiple branches.

# Why (verdict)

Flags like `isManual` describe callers rather than behaviors, forcing readers to trace nested `if (!isManual)` branches to understand what happens (CODE.3). Name flags after what they actually do (e.g., `deadLetterOnError`), or split them into distinct methods when callers want different behavior.

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

The queue trigger calls it with `deadLetterOnError: true` and the delivery count from the message; the manual endpoint calls it with `deadLetterOnError: false` and `deliveryCount: 1`.

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
