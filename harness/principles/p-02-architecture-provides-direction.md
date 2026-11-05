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

Vegviser is the authority for this principle; the applications below record approved harness guidance.[^vegviser] Read the source when a finding depends on the exact wording. A deviation follows Vegviser's Exception and Risk Acceptance playbook.

[^vegviser]: Vegviser Principles, P2

# Application to communication and solution guidance

Prefer asynchronous events for business state changes. Use governed synchronous paths for reads and requests that need an immediate response. Document the permitted path per operation, its contract and failure behavior. Choose the mechanism for the required coupling, latency and consistency; a synchronous query is not inherently a violation of loose coupling.

The harness is product-agnostic. It evaluates service autonomy, stable contracts and loose coupling without requiring a particular broker, gateway, package, platform or project architecture. Project instructions belong to the project. Their underlying rationale may inform general guidance and examples when the evidence and applicability are explicit.

Supporting context: Loop page "Architectural Principles" (A.8-A.20); user decisions 2026-10-29.

# Related guidance

The following rules apply this principle:

- [CODE.10 A derived value has one owner, is never accepted from outside, and says when it becomes consistent](../rules/code/code-10-derived-values-have-one-owner.md).
- [CODE.5 A class does one job and every type lives in its own file](../rules/code/code-5-one-responsibility.md).
- [CODE.7 Files that must change together are linked: listed in the change map, and checked where a check is possible](../rules/code/code-7-linked-changes.md).
- [CODE.8 Capabilities sit behind interfaces and one composition root wires them](../rules/code/code-8-dependencies-point-inward.md).
- [CODE.9 State the input size a component must handle, and shape its algorithm for that size](../rules/code/code-9-shape-the-algorithm-for-its-size.md).
- [DEL.4 A new repo or service starts with its design, written before the code](../rules/delivery/del-4-a-new-service-starts-with-its-design.md).
