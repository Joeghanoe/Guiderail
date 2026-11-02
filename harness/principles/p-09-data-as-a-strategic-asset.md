---
type: Principle
title: "P9 Data as a Strategic Asset"
description: Data is trustworthy, discoverable, governed, reusable and understandable.
principle_id: P9
tags: [data]
status: stable
sources:
  - id: vegviser
    resource: TeamValue.Vegviser@2feca0e:00-foundation/Principles.md#L145-L162
---

# P9 Data as a Strategic Asset

Data is trustworthy, discoverable, governed, reusable and understandable.

Vegviser is the authority for this principle; the applications below record approved harness guidance.[^vegviser] Read the source when a finding depends on the exact wording. A deviation follows Vegviser's Exception and Risk Acceptance playbook.

[^vegviser]: Vegviser Principles, P9

# Application to ownership and sharing

Each service owns its operational write store. Services with separate ownership boundaries do not share mutable operational state. Governed read models for reporting and analytics are permitted, with explicit contracts, ownership and access controls. Replication does not transfer authority to change the source.

Apply this boundary to service ownership rather than requiring separate physical database servers. The harness evaluates ownership and governed access without prescribing a storage or governance product.

Supporting context: Loop page "Architectural Principles" (A.13, A.18), Loop page "Data Principles" (D.10), and user decisions 2026-10-29.
