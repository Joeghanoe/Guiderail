---
type: Principle
title: "P4 Metadata Before Configuration"
description: Describe intent, ownership and behaviour as metadata; configuration executes it.
principle_id: P4
tags: [metadata]
status: stable
sources:
  - id: vegviser
    resource: TeamValue.Vegviser@2feca0e:00-foundation/Principles.md#L76-L87
---

# P4 Metadata Before Configuration

Describe intent, ownership and behaviour as metadata; configuration executes it.

Vegviser is the authority for this principle; this file only points to it.[^vegviser] Read the source when a finding depends on the exact wording. A deviation follows Vegviser's Exception and Risk Acceptance playbook.

[^vegviser]: Vegviser Principles, P4

# Related guidance

The following rules apply this principle:

- [IAC.5 Every resource is declared in code](../rules/iac/iac-5-everything-in-code.md).
- [IAC.7 Per-environment values are configuration; everything fixed is written once in the pipeline](../rules/iac/iac-7-configuration-placement.md).
