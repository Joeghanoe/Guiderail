---
type: Example
title: "E-351 A document database with role assignments still accepts account keys until local auth is disabled"
description: The template grants data-plane roles to the function apps but never sets disableLocalAuth, so the primary keys keep working.
example_id: E-351
rule: /rules/security/sec-3-identity-without-secrets.md
verdict: violation
status: draft
tags: [iac, identity, cosmos, bicep]
example_file: infra/datastore.bicep
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T12:00:00Z }
sources:
  - id: evidence
    resource: aq-infra@Infra/domains/datastore.bicep#L37-L62
  - id: evidence-2
    resource: aq-back@api/Program.cs#L58-L72
---

# Situation

The application connects to the database with a token credential and the endpoint only; the template creates
SQL role assignments for the apps' identities. The account resource has network rules but no
`disableLocalAuth` property, so the default (key access enabled) applies.

# Why (verdict)

SEC.3 asks for `disableLocalAuth: true` on every resource that supports it. With RBAC in place and the keys
still valid, a leaked key or a copied connection string bypasses the roles, the network rules do not cover a
caller from an allowed address, and the key shows up in the portal for anyone with the right to list keys.
The code already needs no key, so the property can be set without a code change; verify in a lower
environment first, because a tool that still uses a key will stop working.

# Compliant pattern

## Good example

```bicep
resource account 'Microsoft.DocumentDB/databaseAccounts@2025-11-01-preview' = {
  name: accountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    disableLocalAuth: true
    databaseAccountOfferType: 'Standard'
    locations: [{ locationName: location, failoverPriority: 0 }]
    ipRules: ipRules
  }
}
```

## Bad example

```bicep
resource account 'Microsoft.DocumentDB/databaseAccounts@2025-11-01-preview' = {
  name: accountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [{ locationName: location, failoverPriority: 0 }]
    ipRules: ipRules
  }
}
```

# Not verified

The storage accounts in the same templates are also reachable by key; see E-352 for why that one is
deliberate. I did not look at the deployed account, only the template.
