---
type: Principle
title: "P11 Standards Enable Innovation"
description: Standards remove needless variation so effort goes to new problems.
principle_id: P11
tags: [standards]
status: stable
sources:
  - id: vegviser
    resource: TeamValue.Vegviser@2feca0e:00-foundation/Principles.md#L183-L192
---

# P11 Standards Enable Innovation

Standards remove needless variation so effort goes to new problems.

Vegviser is the authority for this principle; the applications below record approved harness guidance.[^vegviser] Read the source when a finding depends on the exact wording. A deviation follows Vegviser's Exception and Risk Acceptance playbook.

[^vegviser]: Vegviser Principles, P11

# Application to standards and work instructions

A principle gives durable direction; a standard defines an observable expectation and its scope; a work instruction specifies how to carry it out. Keep authority, exceptions and evidence explicit. Review inferred repository conventions before making them authoritative.

This harness is product-agnostic. Project-specific instructions remain in their projects; useful underlying principles and examples may strengthen general guidance and examples after review. A source's choice of product, platform or project architecture is not a harness requirement.

Use **n-1** for framework currency. [DEL.2](../rules/delivery/del-2-frameworks-n-minus-1.md) defines the supported window as the current stable release or its immediate predecessor. This wording follows the Loop page "Cloud Principles", section "Supported frameworks are always n-1", and the user's wording decision of 2026-10-29.

# Related guidance

The following rules apply this principle:

- [CODE.11 Return early and keep conditional expressions simple](../rules/code/code-11-return-early.md).
- [CODE.3 Names and parameters say what they are for, and flags do not hide logic](../rules/code/code-3-names-say-what-it-is-for.md).
- [DEL.5 The API contract is generated from the code at build time, never written by hand](../rules/delivery/del-5-the-api-contract-is-generated.md).
- [IAC.6 New resources follow the TeamValue naming convention, or the repo's own](../rules/iac/iac-6-naming-convention.md).
