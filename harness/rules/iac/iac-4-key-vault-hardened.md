---
type: Rule
title: "IAC.4 Key Vaults use RBAC, soft delete and purge protection"
description: Key Vaults set enableRbacAuthorization, enableSoftDelete and enablePurgeProtection to true.
rule_id: IAC.4
principle: /principles/p-07-security-by-design.md
tags: [iac, security, keyvault]
applies_to: ["**/*.bicep", "**/*.tf"]
enforced_by: [gate:/gates/iac-settings.md, review]
severity: major
status: stable
sources:
  - id: global
    resource: global.instructions.md (AI Hub main b0cc2ae)
---

# Rule

`enableRbacAuthorization: true`, `enableSoftDelete: true`, `enablePurgeProtection: true`. No access policies.

# Related guidance

This rule applies [P7 Security by Design](../../principles/p-07-security-by-design.md).
