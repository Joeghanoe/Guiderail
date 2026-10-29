---
type: Principle
title: "P2 Architecture Provides Direction"
description: Architecture gives enough direction for teams to decide independently and stay coherent.
principle_id: P2
tags: [architecture]
status: stable
sources:
  - id: vegviser
    resource: TeamValue.Vegviser@2feca0e:00-foundation/Principles.md#L50-L59
---

# P2 Architecture Provides Direction

Architecture gives enough direction for teams to decide independently and stay coherent.

Vegviser is the authority for this principle; this file only points to it.[^vegviser] Read the source when a
finding depends on the exact wording. A deviation follows Vegviser's Exception and Risk Acceptance playbook.

[^vegviser]: Vegviser Principles, P2

# Application to solution guidance

Architecture guidance states its scope and the trade-off it protects. A solution's selected broker,
gateway, package or endpoint is an implementation decision within that scope. Record those decisions
separately so another solution can meet the same intent with a justified implementation.

The supplied Architectural Principles.pdf (A.8-A.20, pp. 5-10) and IntegrationHub Principles.pdf
(IH1-IH6, pp. 1-5) provide supporting context. Service autonomy, stable contracts and loose coupling
guide design; product choices and file-layout conventions require their own scoped standards.
