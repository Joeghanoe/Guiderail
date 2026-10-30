---
type: Example
title: "E-350 Two alerts per probe: one when it reports failure, one when it reports nothing"
description: A failed availability result fires an alert, and so does the absence of any availability result in the window.
example_id: E-350
rule: /rules/observability/obs-2-alerts-follow-causality.md
verdict: compliant
status: draft
tags: [alerts, availability, bicep]
example_file: infra/alerts.bicep
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T12:00:00Z }
sources:
  - id: evidence
    resource: aq-infra@Infra/modules/alerts.bicep#L47-L116
---

# Situation

Function apps run a timer that records an availability result in the telemetry workspace every few minutes.
The template defines two scheduled query alerts on that table.

# Why (verdict)

The first fires when a result says `Success == false`. The second fires when the count of results in the window
is below one, which covers a crashed host, a disabled timer and a broken telemetry pipeline. Silence is treated
as broken, not as healthy (OBS.2). Both alerts are enabled per environment through one parameter and
auto-mitigate when the signal returns.

# Compliant pattern

## Good example

```bicep
resource alertSilent 'Microsoft.Insights/scheduledQueryRules@2022-06-15' = {
  name: 'app-${env}-alert-health-check-silent'
  location: location
  properties: {
    severity: 0
    enabled: alertsEnabled
    evaluationFrequency: 'PT15M'
    windowSize: 'PT15M'
    autoMitigate: true
    scopes: [workspaceId]
    criteria: {
      allOf: [
        {
          query: 'AppAvailabilityResults | summarize TelemetryCount = count()'
          timeAggregation: 'Count'
          operator: 'LessThan'
          threshold: 1
          failingPeriods: { numberOfEvaluationPeriods: 1, minFailingPeriodsToAlert: 1 }
        }
      ]
    }
    actions: { actionGroups: [actionGroup.id] }
  }
}
```

## Bad example

```bicep
resource alertFailed 'Microsoft.Insights/scheduledQueryRules@2022-06-15' = {
  name: 'app-${env}-alert-health-check-failed'
  location: location
  properties: {
    severity: 0
    enabled: alertsEnabled
    evaluationFrequency: 'PT15M'
    windowSize: 'PT15M'
    scopes: [workspaceId]
    criteria: {
      allOf: [
        {
          query: 'AppAvailabilityResults | where Success == false | summarize FailureCount = count()'
          timeAggregation: 'Count'
          operator: 'GreaterThanOrEqual'
          threshold: 1
        }
      ]
    }
    actions: { actionGroups: [actionGroup.id] }
  }
}
```

The bad example is the first half only: a stopped signal never matches `Success == false`.

# Not verified

The silence query counts results across all function apps, so one app going quiet while the others report is
not caught. A query that groups by the reporting app and compares with the list of expected apps would close
that gap; I did not test it.
