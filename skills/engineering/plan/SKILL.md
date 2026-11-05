---
name: plan
description: Decompose complex or multi-layer features into bounded, verifiable work packages with assigned model tiers. Use when planning tasks spanning multiple layers (backend, frontend, infra) or delegating subagent work. Do not use for small, single-file edits.
---

# Workload Planning Discipline

Decompose complex workloads into decoupled packages with explicit handoffs and model tiers.

## Triggers & Scope
- **Use when**: A feature or refactoring touches 3+ layers, spans multiple domains, or benefits from subagent delegation.
- **Skip when**: Changes are localized to a single layer, component, or small bugfix (keep in one thread).

## Core Rules
1. **Split by blast radius**: Group work by bounded context, not by arbitrary folder structures.
2. **Explicit handoffs**: Each package defines inputs, outputs, acceptance criteria, and its own verification command.
3. **Model tiering**: Match task complexity to model tiers (`economy`, `builder`, `reasoner`) to optimize token spend.

## Process & Tooling
Follow the canonical playbook: [orchestrate-workload.md](~/.golden-path-harness/harness/playbooks/orchestrate-workload.md).

1. Check layer complexity:
   `tvh orchestrate layers --raw -- --spec "<task-description>" --report <report.md>`
2. Select model tiers per package:
   `tvh orchestrate tier --raw -- --task "<package-description>"`
3. Decompose workload into packages:
   `tvh orchestrate plan --raw -- --spec <spec.json>`

## Expected Evidence
A structured plan report detailing work packages, dependencies, assigned model tiers, and explicit verification commands.
