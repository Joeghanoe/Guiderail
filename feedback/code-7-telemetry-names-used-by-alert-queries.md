---
type: Example
title: "C-NNN A telemetry event name that an alert query filters on is checked against the code"
description: Event and property names are a contract between the code that sends them and the alert and workbook queries that read them; rename one without a test and the alert goes quiet without an error.
example_id: C-NNN
rule: /rules/code/code-7-linked-changes.md
verdict: violation
status: draft
tags: [code, telemetry, alerts, contracts, observability]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-24T12:00:00Z }
---

# Situation

A worker sends custom events (`RunStarted`, `RunFinished`) with properties in `customDimensions`. Alert rules in Bicep and a workbook query those names as strings. The design doc says that renaming one silences its alert, and a comment in the telemetry class lists the names, but nothing fails when the two sides drift.

# Why (violation)

The names live in two file kinds, C# and KQL inside Bicep, so CODE.4 cannot make them one. Both sides are plain text in the repo and can be read at build time, so CODE.7 asks for a check, not a comment. Without it a rename passes review and the build, and the alert stops firing: the exact failure OBS.2 warns about, caused by a refactor.

# Compliant pattern

Event names are constants in one class. A test reads every alert and workbook file and asserts that each event name a query filters on is one of the constants.

## Good example

```csharp
public static class RunEvents
{
    public const string RunStarted = nameof(RunStarted);
    public const string RunFinished = nameof(RunFinished);

    public static readonly IReadOnlySet<string> All = new HashSet<string> { RunStarted, RunFinished };
}

public class AlertContractTests
{
    private static readonly Regex QueriedEvent = new(@"name\s*==\s*'(?<name>\w+)'", RegexOptions.Compiled);

    [Test]
    public void Every_event_an_alert_queries_is_sent_by_the_worker()
    {
        var queried = Directory.GetFiles(Path.Combine(RepositoryRoot(), "infra", "monitoring"), "*.*")
            .Where(f => f.EndsWith(".bicep") || f.EndsWith(".json"))
            .SelectMany(f => QueriedEvent.Matches(File.ReadAllText(f)).Select(m => m.Groups["name"].Value))
            .Distinct();

        Assert.That(queried.Except(RunEvents.All), Is.Empty, "alert queries name events the worker never sends");
    }
}
```

## Bad example

```csharp
// Event names are queried by infra/monitoring/alerts.bicep; rename one and its alert goes quiet.
public sealed class RunTelemetry(TelemetryClient client)
{
    public void Finished(string runId, string state) =>
        client.TrackEvent("RunFinished", new Dictionary<string, string>
        {
            ["RunId"] = runId,
            ["RunState"] = state,
        });
}
```

# Not verified

The regex only covers `name == '...'`; queries that use `in (...)` or `has` need their own pattern. Property names in `customDimensions` need the same check and are left out to keep the example short.
