---
type: Rule
title: "IAC.5 Every resource is declared in code"
description: Resources exist only through Bicep or Terraform; nothing is created by hand in a portal or console.
rule_id: IAC.5
principle: [/principles/p-04-metadata-before-configuration.md, /principles/p-06-automation-by-default.md]
tags: [iac]
applies_to: ["**/*.bicep", "**/*.tf", "**/*.yml"]
enforced_by: [review]
severity: major
status: stable
---

# Rule

Every resource is declared in Bicep or Terraform and deployed by the pipeline. A resource created by hand, or referenced without being declared or imported as `existing`, is a finding. Names follow [IAC.6](iac-6-naming-convention.md); where values live follows IAC.7.

# Related guidance

This rule applies [P4 Metadata Before Configuration](../../principles/p-04-metadata-before-configuration.md), [P6 Automation by Default](../../principles/p-06-automation-by-default.md).
