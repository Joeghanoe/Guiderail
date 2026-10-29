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

Vegviser is the authority for this principle; this file only points to it.[^vegviser] Read the source when a
finding depends on the exact wording. A deviation follows Vegviser's Exception and Risk Acceptance playbook.

[^vegviser]: Vegviser Principles, P9

# Application to ownership and sharing

Data ownership and governed sharing must identify who can change authoritative state and who consumes
read models. Replication and shared analytical reads require explicit contracts and governance; they do
not imply permission for multiple services to mutate the same operational store.

Loop page "Architectural Principles" (A.13, A.18) and Loop page "Data Principles" (D.10) support this
distinction. The exact boundary of an IT component and any broader restriction on shared read stores
remain scope decisions. A named governance product in a solution instruction does not by itself establish
that product as a company-wide prerequisite.
