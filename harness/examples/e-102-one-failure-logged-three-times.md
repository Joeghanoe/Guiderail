---
type: Example
title: "E-102 One failure is logged, tracked and recorded as a custom event, each with the full exception"
description: A catch block writes the exception to the log, to exception telemetry and into a custom event property, and the timer entry point swallows it silently.
example_id: E-102
rule: /rules/code/code-2-fail-loudly.md
verdict: violation
status: draft
tags: [errors, logging, telemetry]
example_file: src/ProcessFunctions.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T10:00:00Z }
sources:
  - id: evidence
    resource: hub-conn@src/connector-01/ProcessFunctions.cs#L96-L120
  - id: evidence-2
    resource: hub-conn@src/connector-01/ProcessFunctions.cs#L218-L225
---

# Situation

A per-item loop catches `Exception` so that one bad item does not stop the batch. The catch block logs the
exception as a string with `LogCritical`, calls `TrackException`, and then writes `exception.ToString()` into the
`ErrorMessage` property of a custom event.[^evidence] The manual endpoint does the same and returns 500; the timer
entry point catches and only calls `TrackException`.

# Why (verdict)

One failure becomes three records that say the same thing, and the stack trace lands in an event property that an
alert or a report reads (CODE.2, OBS.3). The exception is interpolated into a message string, so the structured
exception is lost. A failure is logged once, with context, in one statement; the event carries a reason code and
the item id. Catching per item to keep the batch going is fine, but the batch result must then say how many items
failed, so the caller can tell a partial run from a clean one.

# Compliant pattern

## Good example

```csharp
foreach (var id in ids)
{
    try
    {
        await ProcessAsync(id, ct);
        succeeded++;
    }
    catch (Exception ex)
    {
        logger.LogError(ex, "Processing item {ItemId} failed", id);   // once, structured
        events.ItemFailed(id, ReasonCode.ProcessingFailed);           // code, not text
        failed++;
    }
}

if (failed > 0)
    throw new BatchFailedException(succeeded, failed);
```

## Bad example

```csharp
catch (Exception ex)
{
    logger.LogCritical($"Error while posting event: {ex}");
    telemetry.TrackException(ex);
    LogCustomEvent(id, "NewApplicant", "1.0", false, ex.ToString());
    operation.Telemetry.Success = false;
}
// the timer entry point: catch (Exception ex) { telemetry.TrackException(ex); }
```

# Not verified

The batch-failure exception in the good example is a sketch; the source has no equivalent. Whether the platform
already de-duplicates the log and the tracked exception was not checked.

[^evidence]: per-item catch block in a processing loop
