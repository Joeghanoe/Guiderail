---
type: Example
title: "E-205 A function app reaches the message bus with the root key, passed as a connection string"
description: The infrastructure module outputs the namespace's root connection string and the function app takes it as a setting; use an identity with a data-receiver role and the namespace name.
example_id: E-205
rule: /rules/security/sec-3-identity-without-secrets.md
verdict: violation
status: draft
tags: [identity, service-bus, bicep]
example_file: modules/servicebus-deployment.bicep
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T09:00:00Z }
sources:
  - id: evidence
    resource: b2b-ext@modules/servicebus-deployment.bicep#L40-L52
  - id: evidence-consumer
    resource: b2b-ext@modules/function-b2b-sync.bicep#L10-L50
---

# Situation

A module deploys a message-bus namespace and outputs `listKeys().primaryConnectionString` of the built-in root authorisation
rule, with the linter's secret-output warning switched off. The next module passes that string into the function app's connection-string
settings.[^evidence]

# Why (verdict)

The root rule can manage, send and listen on the whole namespace, the string travels through deployment outputs and
pipeline parameters, and rotating it means redeploying the consumer. The function app already has a system-assigned
identity (its principal id is output for the vault role assignment), so it can use the same pattern for the bus (SEC.3). With the
Functions host, the setting becomes `ServiceBusConnection__fullyQualifiedNamespace` plus a *Data Receiver* role assignment on
the queue; no secret exists to leak or rotate.

# Compliant pattern

## Good example

```bicep
resource receiver 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: serviceBusQueue
  name: guid(serviceBusQueue.id, functionAppPrincipalId, 'receiver')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4f6d3b9b-027b-4f4c-9142-0e5a2a2247e0') // Azure Service Bus Data Receiver
    principalId: functionAppPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// app setting instead of a connection string:
// ServiceBusConnection__fullyQualifiedNamespace = '<namespace>.servicebus.windows.net'
```

## Bad example

```bicep
resource rootRule 'Microsoft.ServiceBus/namespaces/AuthorizationRules@2024-01-01' existing = {
  parent: serviceBusNamespace
  name: 'RootManageSharedAccessKey'
}

#disable-next-line outputs-should-not-contain-secrets
output serviceBusConnectionString string = rootRule.listKeys().primaryConnectionString
```

# Not verified

Not deployed. The listed role id should be checked against the Azure built-in roles before use. Whether an external
publisher still needs a key was not checked.

[^evidence]: Service-bus and function-app modules of a case-sync function app.
