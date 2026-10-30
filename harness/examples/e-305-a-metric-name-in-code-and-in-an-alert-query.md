---
type: Example
title: "E-305 A metric name written in code and again in an alert query is a linked change"
description: A failure metric emitted by a function and the alert query that sums it by the same string have no check between them.
example_id: E-305
rule: /rules/code/code-7-linked-changes.md
verdict: violation
status: draft
tags: [linked-changes, alerts, telemetry]
example_file: src/ProjectionFunction.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T12:00:00Z }
sources:
  - id: evidence
    resource: aq-back@ruleengine/Functions/ChangeFeedFunction.cs#L50-L77
  - id: evidence-2
    resource: aq-infra@Infra/modules/alerts.bicep#L118-L140
---

# Situation

A function emits a failure count with `TrackMetric("Worker.ChangeFeed.Failures", n)`. The infrastructure
template has an alert whose query is `AppMetrics | where Name == 'Worker.ChangeFeed.Failures' | summarize ...`.
The same string is typed in a C# file and in a Bicep file. The same function also types two other metric names
as literals, one of them in two places.

# Why (verdict)

CODE.4 cannot help across file kinds, so this is the CODE.7 case: rename the metric in code and the alert
keeps running, matches nothing, and stays silent. Nothing fails at build time. The pair is listed in the
repo's change map ("metric names: code constants and alert queries"), the names are constants in one class, and
a test reads the alert template and fails when a name in a query is not a constant in that class.

# Compliant pattern

## Good example

```csharp
public static class MetricNames
{
    public const string ProjectionFailures = "Worker.ChangeFeed.Failures";
    public const string ProjectionBatchSize = "Worker.ChangeFeed.BatchSize";
}

[Fact]
public void Every_metric_used_by_an_alert_exists_in_code()
{
    var bicep = File.ReadAllText(PathToAlertsTemplate);
    var used = Regex.Matches(bicep, @"Name == '([^']+)'").Select(m => m.Groups[1].Value);
    var defined = typeof(MetricNames).GetFields().Select(f => (string)f.GetRawConstantValue()!);

    used.Should().BeSubsetOf(defined);
}
```

## Bad example

```csharp
metrics.TrackMetric("Worker.ChangeFeed.Failures", failures);
```

```bicep
query: '''
AppMetrics
| where Name == 'Worker.ChangeFeed.Failures'
| summarize FailureCount = sum(Sum)
'''
```

# Not verified

I did not check whether the source repo has a change map or a test for this pair; none was visible in the
files I read.
