---
type: Principle
title: "P5 Reuse Before Reinvention"
description: Build on proven patterns and shared capabilities before introducing new approaches.
principle_id: P5
tags: [reuse]
status: stable
sources:
  - id: vegviser
    resource: TeamValue.Vegviser@2feca0e:00-foundation/Principles.md#L88-L97
---

# P5 Reuse Before Reinvention

Build on proven patterns and shared capabilities before introducing new approaches.

Vegviser is the authority for this principle; this file only points to it.[^vegviser] Read the source when a finding depends on the exact wording. A deviation follows Vegviser's Exception and Risk Acceptance playbook.

[^vegviser]: Vegviser Principles, P5

# Related guidance

The following rules apply this principle:

- [CODE.4 A name or key used in more than one place is written once](../rules/code/code-4-write-a-name-once.md).
- [CODE.6 Use what the platform already does before writing it again](../rules/code/code-6-use-what-the-platform-does.md).
- [IAC.7 Per-environment values are configuration; everything fixed is written once in the pipeline](../rules/iac/iac-7-configuration-placement.md).
- [T.6 An adapter is proven once against the real dependency, not only against a stand-in](../rules/testing/t-6-adapter-proven-against-the-real-thing.md).
