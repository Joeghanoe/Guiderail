---
type: Rule
title: "IAC.2 Network access is denied by default"
description: Network ACLs default to Deny with bypass for platform services; public access is off unless the resource is meant to be public.
rule_id: IAC.2
principle: /principles/p-07-security-by-design.md
tags: [iac, network, security]
applies_to: ["**/*.bicep", "**/*.tf"]
enforced_by: [gate:/gates/iac-settings.md, review]
severity: major
status: stable
sources:
  - id: global
    resource: global.instructions.md (AI Hub main b0cc2ae)
---

# Rule

`defaultAction: Deny` and `bypass: AzureServices` on every resource with network ACLs. Public network access is off unless the resource is the public entry point, and then the PR says so. Allowlists name fixed addresses that we own; a shared platform egress address is never allowlisted.
