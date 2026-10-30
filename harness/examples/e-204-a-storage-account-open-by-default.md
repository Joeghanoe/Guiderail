---
type: Example
title: "E-204 A storage account allows public blob access, shared keys and every network"
description: The storage module sets blob public access true, shared-key access true and network default action Allow; set them to the deny side and open exceptions explicitly.
example_id: E-204
rule: /rules/iac/iac-2-network-deny-by-default.md
verdict: violation
status: draft
tags: [bicep, storage, network]
example_file: modules/storage-deployment.bicep
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T09:00:00Z }
sources:
  - id: evidence
    resource: b2b-ext@modules/storage-deployment.bicep#L12-L30
---

# Situation

A Bicep module creates a general-purpose storage account used by function apps for runtime state and a dead-letter container.[^evidence]

# Why (verdict)

The account is `defaultAction: 'Allow'` with `allowBlobPublicAccess: true` and `allowSharedKeyAccess: true`, and OAuth is not
the default. Each container sets `publicAccess: 'None'`, which saves the data today, but the account itself invites the next
container to be made public and reachable from anywhere with a shared key (IAC.2). The deny-by-default shape is: default action
`Deny`, bypass `AzureServices`, no public blob access, identity-based access, and a named network rule where a caller needs in.
TLS 1.2 is already set correctly and stays.

# Compliant pattern

## Good example

```bicep
resource storageAccount 'Microsoft.Storage/storageAccounts@2025-01-01' = {
  name: storageAccountName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    defaultToOAuthAuthentication: true
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Deny'
      virtualNetworkRules: allowedSubnets
    }
  }
}
```

## Bad example

```bicep
properties: {
  defaultToOAuthAuthentication: false
  minimumTlsVersion: 'TLS1_2'
  allowBlobPublicAccess: true
  allowSharedKeyAccess: true
  networkAcls: {
    bypass: 'AzureServices'
    defaultAction: 'Allow'
  }
}
```

# Not verified

Not deployed. A function app on the Functions host may need shared-key access for its own state account; if so, that is a
documented boundary for that account, not for the dead-letter account.

[^evidence]: Storage module of a case-sync function app.
