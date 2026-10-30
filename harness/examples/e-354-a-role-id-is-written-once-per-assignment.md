---
type: Example
title: "E-354 A built-in role id is a named variable, not two copies of a GUID in each assignment"
description: Each role assignment types the same GUID in its name and in its role definition, five times in one module.
example_id: E-354
rule: /rules/code/code-4-write-a-name-once.md
verdict: violation
status: draft
tags: [iac, duplication, bicep]
example_file: infra/functionapp.bicep
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T12:00:00Z }
sources:
  - id: evidence
    resource: aq-infra@Infra/modules/functionapp.bicep#L115-L202
---

# Situation

A module assigns four roles to the function app and a group. In each assignment the role's GUID is typed in the
`guid(...)` that makes the assignment name and again in `subscriptionResourceId(...)`. The GUID has no name,
so a reader must look it up to know it is "Queue Data Contributor".

# Why (verdict)

A value used in more than one place is written once and named (CODE.4). A variable such as
`queueContributorRoleId` removes the second copy, says what the role is, and lets one place change. The same
variables are useful in the other templates that grant these roles.

# Compliant pattern

## Good example

```bicep
var queueDataContributorRoleId = '974c5e8b-45b9-4653-ba55-5f855dd0fb88'

resource queueRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storage
  name: guid(storage.id, app.id, queueDataContributorRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', queueDataContributorRoleId)
    principalId: app.identity.principalId
    principalType: 'ServicePrincipal'
  }
}
```

## Bad example

```bicep
resource queueRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storage
  name: guid(storage.id, app.id, '974c5e8b-45b9-4653-ba55-5f855dd0fb88')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '974c5e8b-45b9-4653-ba55-5f855dd0fb88')
    principalId: app.identity.principalId
    principalType: 'ServicePrincipal'
  }
}
```

# Not verified

Built-in role ids are public Azure constants, not secrets. I did not check the other templates for the same
duplication.
