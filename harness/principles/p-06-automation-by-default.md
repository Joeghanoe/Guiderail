---
type: Principle
title: "P6 Automation by Default"
description: Automate what is repeatable, predictable and deterministic; reliable delivery is the goal.
principle_id: P6
tags: [automation]
status: stable
sources:
  - id: vegviser
    resource: TeamValue.Vegviser@2feca0e:00-foundation/Principles.md#L98-L116
---

# P6 Automation by Default

Automate what is repeatable, predictable and deterministic; reliable delivery is the goal.

Vegviser is the authority for this principle; this file only points to it.[^vegviser] Read the source when a finding depends on the exact wording. A deviation follows Vegviser's Exception and Risk Acceptance playbook.

[^vegviser]: Vegviser Principles, P6

# Related guidance

The following rules apply this principle:

- [DEL.1 Roll forward, never roll back](../rules/delivery/del-1-roll-forward.md).
- [DEL.5 The API contract is generated from the code at build time, never written by hand](../rules/delivery/del-5-the-api-contract-is-generated.md).
- [UI.1 A visual change is looked at, at every screen size, before it is called done](../rules/frontend/ui-1-look-at-what-you-built.md).
- [H.2 Repeated work moves up the automation ladder](../rules/harness/h-2-repeated-work-moves-up.md).
- [IAC.5 Every resource is declared in code](../rules/iac/iac-5-everything-in-code.md).
- [IAC.8 Pipelines call scripts; they do not contain them](../rules/iac/iac-8-pipelines-call-scripts.md).
- [T.1 Done means verified: CI is the full gate, the project verify is the quick local subset](../rules/testing/t-1-done-means-verified.md).
- [T.2 Services do not create their own I/O](../rules/testing/t-2-services-do-not-create-io.md).
- [T.3 Every test runs in its layer, and every layer's gate is in the pipeline](../rules/testing/t-3-tests-run-in-their-layer.md).
