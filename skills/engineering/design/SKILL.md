---
name: design
description: Design a new service, consequential architectural change, or component boundary. Use for greenfield work or a design decision; routine additions within established conventions do not need a new design process.
---

# Design from constraints

Inputs are the requested outcome, approved criteria, current architecture and constraints. A deep module hides substantial implementation behind a small useful interface. A boundary earns its cost through responsibility, substitution or testability; do not invent abstractions for hypothetical future features. Required I/O, time and configuration seams still follow [testing rules](../../../harness/rules/testing/index.md) and [inward dependencies](../../../harness/rules/code/code-8-dependencies-point-inward.md), even with one production adapter.

Load only the route that applies:

- New repository or service: [start greenfield](../../../harness/playbooks/start-greenfield.md). Create and complete the design before source implementation.
- Existing codebase: [discover conventions](../../../harness/playbooks/scaffold-from-conventions.md), then read the affected interfaces, design and accepted ADRs. Extend existing boundaries when they fit.
- Consequential options: [compare alternative designs](COMPARE-ALTERNATIVE-DESIGNS.md). Record trade-offs through the existing architecture decision authority; this skill defines no new ADR format or approval authority.

```bash
tvh greenfield init --target <directory> --profile service
tvh scaffold brief --raw -- --repo <repository> --kind service
tvh verify --repo <repository> --design
```

Output the selected design, constraints, alternatives rejected and remaining decisions. Pass stable interfaces and approved criteria to planning or implementation. A local correction within an established design can proceed without a new ADR.
