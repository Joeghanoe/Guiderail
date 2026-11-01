---
type: Example
title: "E-023 One failure is logged, tracked and recorded as a custom event, each with the full exception"
description: A single error is logged, sent to exception telemetry, and copied into a custom event, creating duplicate records and string-interpolating stack traces.
example_id: E-023
rule: /rules/code/code-2-fail-loudly.md
verdict: violation
status: draft
tags: [errors, logging, telemetry]
example_file: src/ProcessFunctions.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T10:00:00Z }
---

# Situation

A batch loop catches `Exception` so one failure does not halt processing. The catch block logs the error with `LogCritical`, reports it to `TrackException`, and dumps `exception.ToString()` into custom event properties. Downstream entry points duplicate the logging or swallow the error.

# Why (verdict)

A single failure spawns three redundant telemetry records, and interpolating stack traces into custom event properties clutters alert queries and loses structured error data (CODE.2, OBS.3). Log the failure once with context, and let analytics events carry only clean item IDs and reason codes. If catching per-item to continue batch processing, report failure counts explicitly so callers know a run was only partially successful.

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
    LogCustomEvent(id, "ItemReceived", "1.0", false, ex.ToString());
    operation.Telemetry.Success = false;
}
// the timer entry point: catch (Exception ex) { telemetry.TrackException(ex); }
```
