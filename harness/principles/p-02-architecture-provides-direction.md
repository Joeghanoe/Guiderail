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

Vegviser is the authority for this principle; the applications below record approved harness guidance.[^vegviser] Read the source when a
finding depends on the exact wording. A deviation follows Vegviser's Exception and Risk Acceptance playbook.

[^vegviser]: Vegviser Principles, P2

# Application to communication and solution guidance

Prefer asynchronous events for business state changes. Use governed synchronous paths for reads and
requests that need an immediate response. Document the permitted path per operation, its contract and
failure behavior. Choose the mechanism for the required coupling, latency and consistency; a synchronous
query is not inherently a violation of loose coupling.

The harness is product-agnostic. It evaluates service autonomy, stable contracts and loose coupling
without requiring a particular broker, gateway, package, platform or project architecture. Project
instructions belong to the project. Their underlying rationale may inform general guidance and cases
when the evidence and applicability are explicit.

Supporting context: Loop page "Architectural Principles" (A.8-A.20); user decisions 2026-10-29.
