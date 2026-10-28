---
type: Rule
title: "IAC.3 TLS 1.2 or higher only"
description: Minimum TLS 1.2 on every endpoint; TLS 1.0/1.1, SSL 3.0, CBC and TripleDES are off.
rule_id: IAC.3
principle: /principles/p-07-security-by-design.md
tags: [iac, security]
applies_to: ["**/*.bicep", "**/*.tf"]
enforced_by: [gate:/gates/iac-settings.md, review]
severity: major
status: stable
sources:
  - id: global
    resource: global.instructions.md (AI Hub main b0cc2ae)
---

# Rule

Set the minimum TLS version explicitly to 1.2 or higher wherever the resource offers the setting. Do not rely
on the platform default; defaults change and differ per resource type.
