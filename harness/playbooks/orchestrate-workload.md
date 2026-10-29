---
type: Playbook
title: Orchestrate a workload across specialized agents
description: Decompose a milestone, backlog item, or complex change into bounded subagent work packages with cost-effective model tiering and lead review.
tags: [orchestration, workflow, multi-agent]
status: stable
---

# Context

When delivering an epic, phase, or multi-faceted story (e.g. backend + frontend + infrastructure + QA), running a single agent in a single session wastes tokens, causes context bloat, and risks architectural drift. 

Splitting the workload among focused subagents coordinated by a lead orchestration agent delivers faster, cleaner, and cheaper results when combined with **model tiering**:
- Rote checks, linting, and boilerplate do not require a heavy model.
- Standard feature implementation runs efficiently on balanced builder models.
- Deep architectural design, security boundaries, and final integration review use high-reasoning models.

# Input

- The requirement, epic, or issue description (e.g., from backlog or user prompt).
- The repository structure, affected files, and existing verification commands (`dotnet test`, `pnpm test`, etc.).
- Optional: run `python3 ~/.golden-path-harness/harness/tools/orchestration/orchestrate.py plan --spec "<description>" --format markdown`.

# Steps

### 1. Decompose by Domain & Bounded Context
Break down the work into decoupled, single-responsibility roles:
- **`qa-harness-sentinel`**: Guardrails, automated rule enforcement, stack validation, and linting.
- **`<domain>-backend-builder`**: Domain logic, persistence, API endpoints, and backend unit tests.
- **`<domain>-frontend-builder`**: UI components, brand tokens, localization, client state, and component tests.
- **`<domain>-infra-engineer`**: Modular IaC (Bicep / Terraform), cloud resource configuration, zero-secrets validation.
- **`lead-orchestrator-reviewer`**: Workload assignment, four-eyes review, contract testing, and final integration.

### 2. Apply Model Tiering & Token Budgets
For each subagent, select the model tier that minimizes token spend while satisfying task complexity:

| Tier | When to use | Relative Cost |
|---|---|---|
| **Economy** | Lint rules, regex checks, boilerplate, mechanical translations, directory verification | ~0.1x - 0.25x |
| **Builder** | Feature code, React views, EF Core models, ASP.NET endpoints, Bicep modules, unit tests | ~1.0x |
| **Reasoner** | Security & auth design, data model architecture, multi-agent conflict resolution, final review | ~3.0x - 5.0x |

Assign the tier, never a vendor's model name: the tier is the decision, the name is a lookup that differs per
platform and goes stale. Take the tier to whatever model your platform offers for it, the cheapest one that
reliably passes the work package's verification command. If the platform offers one model, the tier still decides
how much context and review the work gets.

To resolve tiers to names for a provider, pass `--provider <name>` (or set `HARNESS_MODEL_PROVIDER`).
`orchestrate.py` reads `models.json` beside it, then `~/.config/harness/models.json`, then `--models FILE`; add
any vendor there, with the date you checked its names. No provider is the default, a provider that is not
configured is an error, and a name older than 120 days is flagged as stale.

Use `python3 ~/.golden-path-harness/harness/tools/orchestration/orchestrate.py tier --task "<subtask>"` to verify the recommended tier.

### 3. Dispatch & Supervise
Launch each subagent with:
- An explicit, bounded task definition and designated file paths.
- The exact verification command that must pass before completion.
- Strict constraint: **Local-first execution** (no git branches or premature commits until the lead agent approves).

### 4. Lead Agent Review & Quality Gate
The lead agent inspects the deliverables:
1. Run all repository test suites (`dotnet test`, `pnpm test`, etc.).
2. Run linters, formatters, and typechecks.
3. Validate that no unauthorized dependencies or secret leaks were introduced.
4. Produce a consolidated summary report and hand off to the user.

# Output

A structured summary report detailing:
1. Subagents deployed, tasks completed, and model tiers used.
2. Verified deliverables and test results.
3. Architecture alignment and git working tree status.
