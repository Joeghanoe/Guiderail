---
type: Example
title: 'E-004 Diagnostics follow their consumers, not "log everything"'
description: A storage account keeps its audit logs; read logs and metric export are only added when an alert or runbook uses them.
example_id: E-004
rule: /rules/iac/iac-1-proportionate-diagnostics.md
verdict: violation
status: stable
verified: { by: human:joeghanoe, at: 2026-10-27T20:07:13Z }
tags: [iac, monitoring, cost]
example_file: infra/storage.bicep
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-19T00:30:00Z }
---

# Situation

A template sends a storage account's blob logs to Log Analytics.

# Why (verdict)

`allLogs` on blob storage includes every read. On a busy account that is the largest line on the monitoring bill, and no alert or workbook reads it. Exporting `AllMetrics` duplicates metrics the platform already keeps. The audit category group keeps who wrote and deleted what, which is what an investigation needs; retention comes from the environment (IAC.1, IAC.7). The default of a setting that costs money every day (retention, daily cap) is the cheap value; an environment that needs more says so in its own variables file.

# Compliant pattern

## Good example

```bicep
param workspaceId string

resource blobs 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' existing = {
  name: '${storageName}/default'
}

resource blobDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'audit-to-log-analytics'
  scope: blobs
  properties: {
    workspaceId: workspaceId
    logs: [
      { categoryGroup: 'audit', enabled: true }   // writes and deletes: who changed what
    ]
  }
}
```

## Bad example

```bicep
param workspaceId string

resource blobs 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' existing = {
  name: '${storageName}/default'
}

resource blobDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'everything-to-log-analytics'
  scope: blobs
  properties: {
    workspaceId: workspaceId
    logs: [
      { categoryGroup: 'allLogs', enabled: true }
    ]
    metrics: [
      { category: 'Transaction', enabled: true }
    ]
  }
}
```

# Not verified

Written for this example in neutral names. Which categories the audit group contains differs per resource type; check the resource's diagnostic categories before relying on it. The 'cheap default' sentence comes from review feedback on one retention parameter; the cost figures were not checked.
