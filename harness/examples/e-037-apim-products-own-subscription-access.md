---
type: Example
title: "E-037 APIM products own subscription access"
description: APIM products own subscription access.
example_id: E-037
rule: /rules/code/code-6-use-what-the-platform-does.md
verdict: violation
status: stable
verified: { by: human:joeghanoe, at: 2026-11-01T19:18:40Z }
tags: [feedback, regression]
generated: { by: codex/unknown, at: 2026-11-01T20:00:00Z }
example_file: infra/access.bicep
---

# Situation

A product-scoped subscription already expresses which APIs its consumer can call. Repeating product membership in operation-name allowlists creates a second access map. Policies still handle authentication, credential forwarding and controls that product membership does not provide.

## Good example

```bicep
resource internalProduct 'Microsoft.ApiManagement/service/products@2024-05-01' existing = {
  name: '${apimName}/internal'
}
resource apiMembership 'Microsoft.ApiManagement/service/products/apis@2024-05-01' = {
  parent: internalProduct
  name: internalApiName
}
resource subscription 'Microsoft.ApiManagement/service/subscriptions@2024-05-01' = {
  name: '${apimName}/internal-client'
  properties: {
    scope: internalProduct.id
    state: 'active'
  }
}
```

## Bad example

```bicep
resource sharedPolicy 'Microsoft.ApiManagement/service/policies@2024-05-01' = {
  name: '${apimName}/policy'
  properties: {
    format: 'rawxml'
    value: '''
<policies><inbound><base /><choose>
<when condition="@(context.Subscription.Name == "internal-client")">
  <choose><when condition="@(!new [] { "get-order", "create-order" }.Contains(context.Operation.Id))">
    <return-response><set-status code="403" reason="Forbidden" /></return-response>
  </when></choose>
</when>
</choose></inbound></policies>
'''
  }
}
```

# Evidence and limits

Prepared from the owner's feedback queue on 2026-11-01. Source snippets use neutral names. Model evaluation tests reviewer behavior, not execution of these snippets. The owner approved this example in the processing session on 2026-11-01. Approval concerns the expected reviewer behavior, not execution of the snippet.
