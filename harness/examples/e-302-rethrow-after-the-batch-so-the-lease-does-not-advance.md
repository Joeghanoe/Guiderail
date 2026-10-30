---
type: Example
title: "E-302 A change-feed handler logs each failed item, counts them, and rethrows once after the batch"
description: Failures inside a batch are not swallowed; the handler finishes the batch, reports a count, and throws so the platform retries.
example_id: E-302
rule: /rules/code/code-2-fail-loudly.md
verdict: compliant
status: draft
tags: [errors, change-feed, retries]
example_file: src/ProjectionFunction.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T12:00:00Z }
sources:
  - id: evidence
    resource: aq-back@ruleengine/Functions/ChangeFeedFunction.cs#L50-L81
---

# Situation

A function is triggered with a batch of changed documents and projects each one into another container. The
platform moves its checkpoint (the lease) forward when the function returns without an exception.

# Why (verdict)

Catching per item and carrying on means one bad document does not block the others, but returning normally
would move the lease past the failed ones and lose them. The handler counts failures, emits a metric with a
stable name, and throws once after the loop with the count, so the batch is delivered again. Each failure is
logged once, at the item, with identifiers and no document content (CODE.2, OBS.3).

# Compliant pattern

## Good example

```csharp
var failures = 0;
foreach (var item in batch)
{
    try
    {
        await projector.SaveAsync(Project(item), ct);
    }
    catch (Exception ex)
    {
        failures++;
        logger.LogError(ex, "Failed to project {ItemId} (tenant {TenantId})", item.Id, item.TenantId);
    }
}

if (failures > 0)
{
    metrics.TrackMetric(MetricNames.ProjectionFailures, failures);
    throw new InvalidOperationException($"{failures} of {batch.Count} items failed; rethrowing so the lease does not advance.");
}
```

## Bad example

```csharp
foreach (var item in batch)
{
    try
    {
        await projector.SaveAsync(Project(item), ct);
    }
    catch (Exception ex)
    {
        logger.LogError(ex, "Failed to project {ItemId}", item.Id);
    }
}
```

# Not verified

The retry re-projects the items that succeeded, so the projection must be idempotent; the source saves by a
stable id, which I read but did not test. The metric name is a literal string in the source (see E-305).
