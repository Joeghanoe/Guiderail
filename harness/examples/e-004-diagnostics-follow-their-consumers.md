---
type: Example
title: 'E-004 Diagnostics follow their consumers, not "log everything"'
description: Export storage audit logs by default, avoiding costly 'allLogs' read streams unless specifically required by alerts or dashboards.
example_id: E-004
rule: /rules/iac/iac-1-proportionate-diagnostics.md
verdict: violation
status: stable
verified: { by: human:teamvaluegroup, at: 2026-10-27T20:07:13Z }
tags: [iac, monitoring, cost]
example_file: infra/storage.bicep
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-19T00:30:00Z }
---

# Situation

An IaC template routes blob storage diagnostic logs to Log Analytics using `allLogs`.

# Why (verdict)

Enabling `allLogs` streams every read operation into Log Analytics, creating massive ingestion costs for unread telemetry (IAC.1). Use the audit category group to track writes and deletes, and configure retention per environment (IAC.7). Default to cost-effective settings unless specific alerts require read telemetry.

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
