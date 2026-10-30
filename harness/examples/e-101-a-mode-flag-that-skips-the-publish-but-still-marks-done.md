---
type: Example
title: "E-101 A boolean mode flag skips the publish but the item is still marked processed"
description: A manual run passes false to skip publishing an event, yet the item is marked processed afterwards, so the event is lost.
example_id: E-101
rule: /rules/code/code-3-names-say-what-it-is-for.md
verdict: violation
status: draft
tags: [naming, flags, data-loss]
example_file: src/ProcessFunctions.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T10:00:00Z }
sources:
  - id: evidence
    resource: hub-conn@src/connector-01/ProcessFunctions.cs#L88-L215
---

# Situation

A timer function and a manual HTTP function share one private method that reads unprocessed items from a vendor
API, publishes an event per item and then marks the item processed in the vendor. The method takes one boolean,
`publishEvent`: the timer passes `true`, the manual endpoint passes `false`.[^evidence]

# Why (verdict)

`false` changes what the method does in two ways that the name does not show: it skips the publish, and the
following `MarkProcessed` call still runs. A manual "dry" run therefore drops every item it touches: the vendor
no longer returns them and no consumer ever saw them. The flag hides two behaviours behind one word (CODE.3).
The caller decides: either the manual endpoint calls only the read and returns the items, or the method is split
into `Publish` and `Preview`, and only the publishing path marks items done.

# Compliant pattern

## Good example

```csharp
// Manual endpoint: reads and reports, changes nothing in the vendor.
public Task<IReadOnlyList<Applicant>> PreviewApplicantsAsync(CancellationToken ct) =>
    vendor.GetUnprocessedApplicantsAsync(ct);

// Timer: publish, then mark done. Marking is part of publishing, not a separate step.
public async Task PublishApplicantsAsync(CancellationToken ct)
{
    foreach (var applicant in await vendor.GetUnprocessedApplicantsAsync(ct))
    {
        await events.PublishAsync(applicant, ct);
        await vendor.MarkProcessedAsync(applicant.Id, ct);
    }
}
```

## Bad example

```csharp
private async Task ProcessApplicants(bool publishEvent)
{
    foreach (var id in await vendor.GetUnprocessedIds())
    {
        var applicant = await vendor.GetApplicant(id);
        if (publishEvent)
            await events.Publish(applicant);
        else
            logger.LogInformation("Manual run, skipping publish.");

        await vendor.MarkProcessed(id);   // runs for both values
    }
}
```

# Not verified

Whether the manual endpoint is meant to consume items is not documented in the source; the behaviour was read
from the code only.

[^evidence]: shared private method with a publish flag, called by a timer and a manual endpoint
