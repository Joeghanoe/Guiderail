---
type: Example
title: "E-005 Resource names follow one convention, built from the environment name"
description: Standardize cloud resource naming conventions across environments using consistent variable patterns rather than ad-hoc names.
example_id: E-005
rule: /rules/iac/iac-6-naming-convention.md
verdict: violation
status: stable
verified: { by: human:teamvaluegroup, at: 2026-10-27T20:07:13Z }
tags: [naming, pipelines]
example_file: pipelines/build-and-deploy.yml
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-19T00:00:00Z }
---

# Situation

A pipeline defines Azure resource names individually with mixed casing, inconsistent prefixes, and irregular abbreviations.

# Why (verdict)

Ad-hoc resource names make it hard to identify ownership, workload, and environment at a glance. Standardize on a predictable naming pattern parameterized by environment name to ensure consistency by design ([IAC.6](../rules/iac/iac-6-naming-convention.md)).

# Compliant pattern

## Good examples

```yaml
variables:
  - name: resourceGroupName
    value: orders-${{ environment.name }}-we-rg
  - name: functionAppName
    value: orders-api-${{ environment.name }}-we-func
  - name: keyVaultName
    value: orders-${{ environment.name }}-we-kv
  - name: storageAccountName      # no hyphens allowed: same parts, same order
    value: ordersapi${{ environment.name }}west
```

or

```yaml
variables:
  - resourceGroupName: orders-${{ environment.name }}-we-rg
  - functionAppName: orders-api-${{ environment.name }}-we-func
  - keyVaultName: orders-${{ environment.name }}-we-kv
  - storageAccountName: ordersapi${{ environment.name }}west
```

## Bad example

```yaml
variables:
  - name: resourceGroupName
    value: rg-orders-${{ environment.name }}
  - name: functionAppName
    value: OrdersApiFunction-${{ environment.name }}
  - name: keyVaultName
    value: kv-orders-prod-01
  - name: storageAccountName
    value: ordersstorage01
```

# Variant: the type part is the real type, and a file is named for what it deploys

A name says what the resource is. The `type` part is the abbreviation of the actual resource type, and the name does not carry a second, wrong description of it. A file is named for what it deploys, without words that only repeat the folder or the parent.

```bicep
// Good: the workload, the environment, the region, the type.
resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'orders-${environment}-we-id'
  location: location
}

// Bad: "ManagedIdentity" in the name of a user-assigned identity, no environment, no region, no type.
resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'orders-ManagedIdentity'
  location: location
}
```

Likewise `orders.bicep` is enough for the template of the orders workload; `orders.catchall.bicep` repeats the name of a component that already has its own module.

# Not verified

Written for this example in neutral names. A repo with its own established convention follows that one instead ([IAC.6](../rules/iac/iac-6-naming-convention.md)). The variant comes from review feedback on one set of templates; the type abbreviation `id` follows [IAC.6](../rules/iac/iac-6-naming-convention.md)'s table, which a repo may replace with its own.
