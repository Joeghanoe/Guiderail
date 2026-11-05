---
type: Example
title: "E-003 Storage clients authenticate with managed identity"
description: Authenticate storage clients using DefaultAzureCredential and service endpoints rather than connection strings with account keys.
example_id: E-003
rule: /rules/security/sec-3-identity-without-secrets.md
verdict: violation
status: stable
verified: { by: human:teamvaluegroup, at: 2026-10-20T19:47:15Z }
tags: [identity, storage, azure]
example_file: src/Program.cs
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-18T23:00:00Z }
---

# Situation

An application registers Azure Blob Storage clients using connection strings containing raw account keys.

# Why (verdict)

Connection strings contain long-lived access keys that grant full access from any location if leaked ([SEC.3](../rules/security/sec-3-identity-without-secrets.md)). Authenticate using `DefaultAzureCredential` with managed identities, granting least-privilege access via Azure RBAC.

# Compliant pattern

## Good example

```csharp
builder.Services.AddAzureClients(clients =>
{
    clients.AddBlobServiceClient(new Uri(builder.Configuration["Storage:BlobEndpoint"]!));
    clients.UseCredential(new DefaultAzureCredential());
});
```

## Bad example

```csharp
builder.Services.AddSingleton(
    new BlobServiceClient(builder.Configuration["Storage:ConnectionString"]));
```

# Variant: grant only the roles the identity uses

Access is also what you grant. An identity that only publishes to one topic gets one role on that topic, not a role on the whole namespace, and not a second role that an existing one already includes.

```bicep
param topicName string
param gatewayPrincipalId string
param eventGridDataSenderRoleId string

resource topic 'Microsoft.EventGrid/topics@2022-06-15' existing = {
  name: topicName
}

// Good: the gateway publishes to the topic, nothing else.
resource publish 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: topic
  name: guid(topic.id, gatewayPrincipalId, eventGridDataSenderRoleId)
  properties: {
    principalId: gatewayPrincipalId
    roleDefinitionId: eventGridDataSenderRoleId
    principalType: 'ServicePrincipal'
  }
}

param namespaceName string
param gatewayPrincipalId string
param serviceBusDataSenderRoleId string
param contributorRoleId string
param readerRoleId string

resource namespace 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' existing = {
  name: namespaceName
}

// Bad: a topic-only publisher also receives namespace-wide roles it does not use.
resource queueSender 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: namespace
  name: guid(namespace.id, gatewayPrincipalId, serviceBusDataSenderRoleId)
  properties: {
    principalId: gatewayPrincipalId
    roleDefinitionId: serviceBusDataSenderRoleId
    principalType: 'ServicePrincipal'
  }
}

resource namespaceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: namespace
  name: guid(namespace.id, gatewayPrincipalId, contributorRoleId)
  properties: {
    principalId: gatewayPrincipalId
    roleDefinitionId: contributorRoleId
    principalType: 'ServicePrincipal'
  }
}

resource namespaceReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: namespace
  name: guid(namespace.id, gatewayPrincipalId, readerRoleId)
  properties: {
    principalId: gatewayPrincipalId
    roleDefinitionId: readerRoleId
    principalType: 'ServicePrincipal'
  }
}
```

# Not verified

Written for this example in neutral names; not taken from one project.
