---
type: Rule
title: "T.6 An adapter is proven once against the real dependency, not only against a stand-in"
description: Every adapter to an external system has at least one test that runs it against the real system, or against a recorded real response, so the shapes and the timing its code depends on are observed, not assumed.
rule_id: T.6
principle: [/principles/p-08-observable-by-design.md, /principles/p-05-reuse-before-reinvention.md]
tags: [testing, integration, adapters, fakes, stubs]
applies_to: ["**/*.cs", "**/*.ts", "**/*.py", "**/*Tests*/**", "**/tests/**"]
enforced_by: [review]
severity: major
status: stable
approval_commit: cae82ed
sources:
  - id: origin
    resource: FoodApp portal build (2026-10-31): the adapter tests passed against hand-written Directus JSON while the real Directus lacked the one-to-many field that exposes a recipe's lines, and ran its hooks after the response returned. Only the end-to-end journey against a real instance found both.
---

# Rule

- An adapter is the class or module that talks to a system you do not own the code of: an HTTP service, a database, a queue, an identity provider, a CLI. Each adapter has at least one test that runs it against the **real** system, or against a **recorded real response** captured from it. Layer 0 or 1 ([T.3](t-3-tests-run-in-their-layer.md)): a container, an emulator or a local instance; never a paid or shared cloud service, which belongs in layer 2 with test tenants.
- A recorded response carries its provenance next to it (what was called, when, which version), and is refreshed when the dependency is upgraded. A response written by hand from the documentation or from memory is a stand-in, not evidence.
- The real-dependency test looks at what the code depends on and a stub can get wrong: field names and nesting, a field that is absent versus null, numbers that arrive as strings, pagination, the shape of an error body, permissions that hide a field, and **timing** (is the effect of a write visible when the call returns?).
- Stubs and fakes stay for speed and for failure injection (a timeout, a 500). They are not removed; they are no longer the only proof.
- The design says, for each stand-in used in tests, which real-dependency test backs it (the "Components" section of the solution design, [DEL.4](../delivery/del-4-a-new-service-starts-with-its-design.md)).

# Boundary

A pure mapper with no I/O needs no real dependency. A dependency that cannot run locally and has no recordable response (a vendor sandbox that needs a tenant) gets its test in layer 2, named in the design, and the adapter is not called proven until it has run there.

# Check

Review lists each adapter and finds its real-dependency test or recorded response; a missing one, or a fixture whose only source is the author, is a major finding that cites T.6.

# Related guidance

This rule applies [P8 Observable by Design](../../principles/p-08-observable-by-design.md), [P5 Reuse Before Reinvention](../../principles/p-05-reuse-before-reinvention.md).
