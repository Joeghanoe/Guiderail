---
type: Case
title: "C-NNN Express subscription access through API products, not operation-name lists"
description: A shared policy duplicated product membership by branching on subscription and operation identifiers.
case_id: C-NNN
rule: /rules/code/code-6-use-what-the-platform-does.md
verdict: violation
status: draft
tags: [apim, api-gateway, access, products, policy]
generated: { by: copilot-sdk/unknown, at: 2026-10-21T11:29:30Z }
sources:
  - id: evidence
    resource: pull request review thread on a shared auth-headers policy fragment; the original policy is not present in the implementation snapshot
  - id: implementation
    resource: LMN.Shared.APIM@5eee7fa:src/applications/sap/api.bicep#L52-L105
  - id: product-membership
    resource: LMN.Shared.APIM@5eee7fa:src/applications/sap/api.bicep#L117-L138
  - id: subscription-scope
    resource: LMN.Shared.APIM@5eee7fa:src/products/digital-api/internal.bicep#L50-L58
  - id: policy-responsibilities
    resource: LMN.Shared.APIM@5eee7fa:src/applications/sap/external-policies.xml#L20-L26
  - id: internal-product-policy
    resource: LMN.Shared.APIM@5eee7fa:src/products/digital-api/internal-policy.xml#L20-L29
---

# Situation

A gateway exposed internal and external API surfaces over the same service. The feedback reports that a
proposed shared policy identified callers by subscription id and kept operation-name allowlists for deciding
which surface a caller could use. The resulting implementation instead creates distinct internal and external API
definitions, gives them separate paths and policies, and attaches each to its corresponding product.[^implementation]

The distinction is not “products replace every policy.” The external API policy adds the internal product's
subscription key when forwarding to the internal API, while the internal product policy validates bearer
tokens. These are separate concerns: product subscription scope expresses which APIM surface a subscription
can call; policies still handle authentication and gateway-to-backend/API behavior.[^policy]

# Why (verdict)

CODE.6 and P5: APIM products and product-scoped subscriptions already express subscription-based API access.
Repeating product membership as a set of operation-name checks in a shared policy creates a second access
map that must be kept in sync with API definitions and product membership. Adding an operation then requires
remembering to update policy lists as well as the API/product configuration.

Use product membership for subscription admission and reserve policies for controls the product boundary
does not provide, such as validating a bearer token or supplying a credential for a downstream APIM call.
Do not infer that product membership alone implements every caller-authorization requirement.

## Compliant pattern

- Create separate API definitions when internal and external callers need distinct paths, contracts, or
  policy behavior, even when both ultimately use the same service.
- Attach each API definition to its intended product using the product membership resource.
- Scope the subscription to that product when subscription-based admission is intended.
- Keep policy logic for authentication, credential forwarding, and other requirements that are not product
  membership.

## Good example

```bicep
module addExternalApiToProducts 'add-api-to-multiple-products.bicep' = {
  name: 'add-external-api-to-products'
  params: {
    apimResourceName: apimResourceName
    productNames: externalProducts
    apiName: externalApi.outputs.apiName
  }
}

module addInternalApiToProducts 'add-api-to-multiple-products.bicep' = {
  name: 'add-internal-api-to-products'
  params: {
    apimResourceName: apimResourceName
    productNames: internalProducts
    apiName: internalAPI.outputs.apiName
  }
}
```

The implementation separately defines the internal and external APIs before attaching them to their product
arrays.[^implementation] Its external policy forwards the internal product key to the internal API; that is
downstream authentication, not an operation allowlist.[^policy]

## Bad example

```xml
<choose>
    <when condition="@(context.Subscription.Id == &quot;automation&quot;)">
        <!-- Permit only a hard-coded list of operation IDs. -->
    </when>
    <otherwise>
        <!-- Deny that list, or maintain a second list for other callers. -->
    </otherwise>
</choose>
```

This duplicates product/API membership in a shared policy and makes every operation change depend on keeping
the lists current. The exact prior policy is reported by the review thread; it is not included in the current
source snapshot.[^evidence]

# Not verified

The implementation snapshot supports separate API definitions, product membership, and a product-scoped
subscription. It does not establish that the historical shared policy used precisely the operation lists
described in the review thread, nor that moving an existing subscription between products preserves its
keys on every APIM tier. Verify key continuity in a non-production environment before any such migration.

[^evidence]: Review-thread summary supplied with the draft feedback; the original thread and prior policy were not available for this check.
[^implementation]: SAP API module declares separate internal/external product arrays and attaches the separate API definitions to those arrays.
[^policy]: The external API policy sets `Ocp-Apim-Subscription-Key` from a named value; the internal product policy separately validates bearer JWTs.
