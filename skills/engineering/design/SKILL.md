---
name: design
description: Design system architecture, service structure, component interfaces, and boundaries. Use when starting a greenfield project, introducing architectural patterns, or evaluating consequential technical decisions.
---

# Codebase & System Design Discipline

Design deep modules with minimal interface surface and high caller leverage.

## Triggers & Scope
- **Use when**: Initializing a repository/service, introducing new architectural boundaries, or designing modules/interfaces.
- **Skip when**: Adding routine endpoints or components within established conventions.

## Core Rules
1. **Deep Modules**: Strive for interfaces that are small and simple relative to the power and complexity hidden behind them.
2. **The Deletion Test**: A module earns its keep only if deleting it would cause significant complexity to reappear across multiple callers.
3. **Seam Discipline**: Do not create speculative abstractions or adapters. *One adapter means a hypothetical seam; two concrete adapters mean a real one.*
4. **Inward Dependencies (CODE.8)**: Domain logic depends strictly on abstractions; persistence, cloud, and transport layers point inward.
5. **Testability by Design**: Accept dependencies (DI), return results instead of emitting side effects, and keep the public test seam focused.

## Process & Tooling
Follow canonical playbooks:
- **Starting greenfield**: [start-greenfield.md](~/.golden-path-harness/harness/playbooks/start-greenfield.md)
  `tvh greenfield init --template dotnet-react --out <dir>`
- **Extending existing codebase**: [scaffold-from-conventions.md](~/.golden-path-harness/harness/playbooks/scaffold-from-conventions.md)
  `tvh scaffold conventions --raw -- --root <repo>`
- **Validate type & architecture boundaries**:
  `tvh checks code-types --json -- --repo <repo>`

## Expected Evidence
A recorded design decision (ADR or specification design section), passing design gates, and explicit interface boundaries.
