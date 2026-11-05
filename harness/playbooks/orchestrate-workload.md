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

# Trigger

`tvh orchestrate layers --raw -- --spec "<task>" --report REPORT.md` counts the layers a task touches; three or more means this playbook applies. It exits 3 until the report holds the plan or a named reason for one thread (`Decomposition: single thread - <reason>`).

# Input

- The requirement, epic, or issue description (e.g., from backlog or user prompt).
- The repository structure, affected files, and existing verification commands (`dotnet test`, `pnpm test`, etc.).
- Optional: run `tvh orchestrate plan --raw -- --spec "<description>" --format markdown`.

# Steps

### 1. Decompose by Domain & Bounded Context

Break down the work into decoupled, single-responsibility roles:

- **`qa-harness-sentinel`**: Guardrails, automated rule enforcement, stack validation, and linting.
- **`<domain>-backend-builder`**: Domain logic, persistence, API endpoints, and backend unit tests.
- **`<domain>-frontend-builder`**: UI components, brand tokens, localization, client state, and component tests.
- **`<domain>-infra-engineer`**: Modular IaC (Bicep / Terraform), cloud resource configuration, zero-secrets validation.
- **`lead-orchestrator-reviewer`**: Workload assignment, four-eyes review, contract testing, and final integration.

Then audit the edges before fanning out. "And then" is not a dependency: for each arrow, name the output the next work package reads. If you cannot name it, the packages are independent and run in parallel. Split by blast radius (what a change can break), not by folder, so packages do not audit the same files. Read the constraints left by earlier accepted work (see _Learning edge_) before cutting.

### 2. Apply Model Tiering & Token Budgets

For each subagent, select the model tier that minimizes token spend while satisfying task complexity:

| Tier | When to use | Relative Cost |
| --- | --- | --- |
| **Economy** | Lint rules, regex checks, boilerplate, mechanical translations, directory verification | ~0.1x - 0.25x |
| **Builder** | Feature code, React views, EF Core models, ASP.NET endpoints, Bicep modules, unit tests | ~1.0x |
| **Reasoner** | Security & auth design, data model architecture, multi-agent conflict resolution, final review | ~3.0x - 5.0x |

Assign the tier, never a vendor's model name: the tier is the decision, the name is a lookup that differs per platform and goes stale. Take the tier to whatever model your platform offers for it, the cheapest one that reliably passes the work package's verification command. If the platform offers one model, the tier still decides how much context and review the work gets.

To resolve tiers to names for a provider, pass `--provider <name>` (or set `HARNESS_MODEL_PROVIDER`). `tvh orchestrate tier` reads [models.json](../tools/orchestration/models.json) beside it, then `~/.config/harness/models.json`, then `--models FILE`; add any vendor there, with the date you checked its names. No provider is the default, a provider that is not configured is an error, and a name older than 120 days is flagged as stale.

Use `tvh orchestrate tier --raw -- --task "<subtask>"` to verify the recommended tier.

### 3. Dispatch & Supervise

Launch each subagent with:

- An explicit, bounded task definition and designated file paths.
- The exact verification command that must pass before completion.
- Strict constraint: **Local-first execution** (no git branches or premature commits until the lead agent approves).
- A fresh context and a brief (objective, files, decisions, open questions), never the lead's transcript. Workers that share a window converge on one opinion; independent contexts give independent findings. The reviewer runs in its own context, never the builder's.
- The autonomy rung: `investigate` (report, touch nothing), `draft` (prepare, a human approves) or `autopilot` (act, verify, ship on green). Start new kinds of work on `draft`; move up only after five clean runs in a row, and step back a rung the moment the work touches anything live. A hard-to-reverse change (migration, deletion, production data, money) has no autopilot rung at all (CLD.2); this is a closed lane, not a high threshold.
- Merging, ranking, deduplicating and before/after comparisons are scripts, not model calls. If the step can be described without _judge, decide, assess_ or _summarize_, it is code.

Keep sessions small: one job per session, state in a file of at most ten lines (done, decisions, file names, next step), and start a fresh session when the context grows past roughly 120K tokens. Wake the lead only when a package is done with proof, needs a decision, or is blocked.

### 3a. Define a check that can fail

Every work package names a verification command that exits non-zero when the work is wrong, written before the work starts. These are not checks: "the output looks good", "the model is confident", "no errors were raised". Absence of an error is not evidence of correctness.

### 3b. Return the unit, not the batch

When one package fails, return only that package; never rework the ones that passed. A return carries:

| Field    | Content                                       |
| -------- | --------------------------------------------- |
| Unit     | the package or file                           |
| Verdict  | red                                           |
| Reason   | the failing check                             |
| Evidence | the output, with `file:line`                  |
| Scope    | what to fix, and that nothing else may change |

Without the scope line a returned unit grows into an unreviewed multi-file diff. After three failed corrections of one unit, stop: the fault is in the plan, so go back to step 1. A verdict that changes nothing that runs next is only a report.

### 3c. Learning edge

When the lead accepts a result, write the general constraint it implies (a principle, not the incident; it must make sense to someone who was not there) into the brief that step 1 reads for later packages. A confirmed cause becomes a rule, so the next failure starts where this one ended. If a tool could decide it, take it to [process-feedback.md](process-feedback.md) (H.2).

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
4. The autonomy rung used per package, returns per package, and the constraints written back (step 3c).
