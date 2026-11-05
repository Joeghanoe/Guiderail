---
type: Rule
title: "CODE.5 A class does one job and every type lives in its own file"
description: A class owns one responsibility, the decision about a dependency stays in the class that talks to it, unrelated entry points live in separate classes, and each type has its own file.
rule_id: CODE.5
principle: /principles/p-02-architecture-provides-direction.md
tags: [code, design]
applies_to: ["**/*.cs", "**/*.ts", "**/*.tsx", "**/*.bicep"]
enforced_by: [gate:/gates/code-types.md, review]
severity: minor
status: stable
verified: { by: human:teamvaluegroup, at: 2026-10-18T18:52:51Z }
sources:
  - id: origin
    resource: recurring pull request review feedback, 2023-2026, one platform team
---

# Rule

- C# declaration layout follows the [executable checker](/tools/code/Program.cs), through the [CODE.5 gate](/gates/code-types.md). For TypeScript, each component, hook or exported type has its own matching file. Types used by a service live next to it rather than accumulating in its implementation file.
- Do not add an interface or wrapper only to justify a file.
- An entry point that has nothing to do with the rest of the class (a health endpoint next to business functions) is its own class.
- The class that talks to a dependency decides what the dependency's answer means. Its raw response does not leave the class; callers get the decision.
- Files for different deployment targets (local development versus a published product) are kept apart, so they cannot grow into each other.
- A shared helper has a shared home, not a copy per project.

# Boundary

A type nested inside its only user and private to it (a nested private enum or helper record) may stay in that file. A sibling top-level type may not, however small.

On a touched mixed file, split out the types the change adds or changes; do not refactor the whole file.

# Executable scope

The C# checker is authoritative for generated-file detection, partial filenames, nested visibility and declaration comparison. Its regression fixtures live in [test_code_types.py](../../../tests/test_code_types.py) in the harness repository. Do not maintain a second list of those mechanics here or infer responsibility from a structural pass.

The scope was approved on 2026-10-29. Semantic ownership, responsibility and the single-user condition on private helpers remain review concerns.
