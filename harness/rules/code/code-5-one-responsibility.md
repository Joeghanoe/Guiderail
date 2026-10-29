---
type: Rule
title: "CODE.5 A class does one job and every type lives in its own file"
description: A class owns one responsibility, the decision about a dependency stays in the class that talks to it, unrelated entry points live in separate classes, and each type has its own file.
rule_id: CODE.5
principle: /principles/p-02-architecture-provides-direction.md
tags: [code, design]
applies_to: ["**/*.cs", "**/*.ts", "**/*.tsx", "**/*.bicep"]
enforced_by: [review]
severity: minor
status: stable
verified: { by: human:joeghanoe, at: 2026-10-18T18:52:51Z }
sources:
  - id: origin
    resource: recurring pull request review feedback, 2023-2026, one platform team
---

# Rule

- One type per file, named like the file: class, interface, record, enum, service, validator and, in
  TypeScript, a component, hook or exported type. A service has many methods; the types it uses live next to
  it in their own files.
- Do not add an interface or wrapper only to justify a file.
- An entry point that has nothing to do with the rest of the class (a health endpoint next to business
  functions) is its own class.
- The class that talks to a dependency decides what the dependency's answer means. Its raw response does not
  leave the class; callers get the decision.
- Files for different deployment targets (local development versus a published product) are kept apart, so
  they cannot grow into each other.
- A shared helper has a shared home, not a copy per project.

# Boundary

A type nested inside its only user and private to it (a nested private enum or helper record) may stay in that
file. A sibling top-level type may not, however small.

On a touched mixed file, split out the types the change adds or changes; do not refactor the whole file.

For the C# structural check, generated files are excluded. Partial declarations may live in separate
files named `Type.cs` or `Type.Part.cs`. The private nested-type exception still applies. Compare
against a baseline to evaluate added or changed declarations separately from inherited violations.

This scope was approved by the user on 2026-10-29. The Roslyn checker in `tools/code/` emits JSON
structural evidence; responsibility and the other design expectations remain review concerns.
