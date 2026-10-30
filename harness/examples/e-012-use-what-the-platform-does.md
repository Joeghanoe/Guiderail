---
type: Example
title: "E-012 A gateway policy does not repeat what the gateway already enforces"
description: An API that requires a subscription key does not also check the key in every operation policy; request shapes are validated once at the front with the platform's validation.
example_id: E-012
rule: /rules/code/code-6-use-what-the-platform-does.md
verdict: violation
status: stable
verified: { by: human:joeghanoe, at: 2026-10-27T20:07:13Z }
tags: [apim, api, validation]
example_file: infra/api.bicep
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T21:00:00Z }
sources:
  - id: evidence
    resource: pull request review threads asking why a policy re-implements gateway behaviour (mined 2026-10-18)
---

# Situation

An API behind a gateway is secured with a subscription key. Each operation has its own policy that checks
that a key is present and that the body has the right fields, written by hand.

# Why (verdict)

With `subscriptionRequired: true` the gateway rejects a call without a valid key before any policy runs;
the same check in each operation is code that can only drift. Request bodies are validated once, at the front,
with a schema on the operation and a `validate-content` policy, so that bad requests are stopped before
processing and the contract is documented in the same place. If a hand-written check is needed (the platform
returns 500 where a client needs a 4xx), a comment says so (CODE.6).

# Compliant pattern

## Good example

```bicep
resource api 'Microsoft.ApiManagement/service/apis@2023-09-01-preview' = {
  parent: gateway
  name: 'events'
  properties: {
    displayName: 'Events'
    path: 'events'
    protocols: ['https']
    subscriptionRequired: true      // the gateway rejects calls without a valid key
  }
}

resource publishPolicy 'Microsoft.ApiManagement/service/apis/operations/policies@2023-09-01-preview' = {
  parent: publishOperation
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: '''
      <policies><inbound><base />
        <validate-content unspecified-content-type-action="prevent" max-size="102400" size-exceeded-action="prevent" errors-variable-name="errors">
          <content type="application/json" validate-as="json" action="prevent" />
        </validate-content>
      </inbound></policies>
    '''
  }
}
```

## Bad example

```bicep
resource api 'Microsoft.ApiManagement/service/apis@2023-09-01-preview' = {
  parent: gateway
  name: 'events'
  properties: {
    displayName: 'Events'
    path: 'events'
    protocols: ['https']
    subscriptionRequired: true
  }
}

resource publishPolicy 'Microsoft.ApiManagement/service/apis/operations/policies@2023-09-01-preview' = {
  parent: publishOperation
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: '''
      <policies><inbound><base />
        <choose>
          <when condition="@(string.IsNullOrEmpty(context.Subscription?.Key))">
            <return-response><set-status code="401" /></return-response>
          </when>
        </choose>
        <choose>
          <when condition="@(context.Request.Body.As<JObject>(true)["type"] == null)">
            <return-response><set-status code="400" /></return-response>
          </when>
        </choose>
      </inbound></policies>
    '''
  }
}
```

# Not verified

Written for this example in neutral names. A schema attached to an operation documents the contract but does
not validate by itself; validation needs the `validate-content` policy. Check the gateway's behaviour for
your SKU before you delete a hand-written check.
