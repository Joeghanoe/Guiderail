---
type: Rule
title: "SEC.3 Services authenticate with an identity, not a secret"
description: Managed identity and RBAC inside a tenant, a federated credential across tenants; no keys or connection strings.
rule_id: SEC.3
principle: /principles/p-07-security-by-design.md
tags: [security, identity, azure]
applies_to: ["**/*.cs", "**/*.ts", "**/*.bicep", "**/*.tf", "**/*.json"]
enforced_by: [review]
severity: blocker
status: stable
sources:
  - id: global
    resource: global.instructions.md (AI Hub main b0cc2ae)
---

# Rule

- Inside a tenant: managed identity (`DefaultAzureCredential`) with RBAC. No connection strings, account
  keys, SAS tokens or access policies.
- Grant RBAC at the narrowest scope (the resource, not the subscription or resource group) and the narrowest
  built-in role that does the job.
- `disableLocalAuth: true` on every resource that supports it.
- Across tenants or clouds: a federated credential (workload identity, signed client assertion).
  A certificate is the fallback. A client secret is a last resort and needs a rotation date.

# Boundary

A third party that only offers a key (an external API, APIM subscriptions for customers) is allowed. The key
lives in Key Vault, is read through the service's identity, and is named in the PR.
