# ADR 0002: Agentic SDLC and Harness Principles

- **Status:** Draft — discovery and review required
- **Date:** 2026-10-29
- **Scope:** Shared agent execution standards and evaluation boundaries
- **Depends on:** ADR 0001

## Context

The Golden Path needs a repeatable agent-assisted engineering implementation that is consistent across Claude Code, Codex, and future tools. Company principles are the source of intent; two reference repositories provide evidence of conventions, but are not automatically correct. Roughly 8–10 example projects can be audited and used for greenfield/brownfield evaluation.

## Proposed decision (not yet ratified)

1. **Principles precede tools.** Company architectural principles and approved conventions define required outcomes. Agent-specific prompts and skills only implement them.
2. **The harness is an execution and enforcement mechanism, not the source of business truth.** It reads an approved, versioned story/specification, operates within scoped permissions, and emits auditable artifacts.
3. **Rules should be executable where possible.** Use deterministic analyzers, tests, and policy scripts for objective constraints (for example, .NET file/class structure). Behavioral evals assess agent decisions and truthful reporting. Functional acceptance evals measure delivered behavior.
4. **Keep execution and evaluation independent.** The candidate must not modify evaluator rules, hidden acceptance fixtures, or approval thresholds during a run.
5. **Model-neutral contracts.** Scenarios, checks, results, and evidence should not depend on a single agent provider. Differences in tools and execution context must be disclosed in comparisons.
6. **Controlled feedback loop.** Greenfield evaluations first; introduce brownfield projects incrementally. Audit pre-existing violations separately from agent-introduced violations. Classify disagreements as project, evaluator, principle, or evidence problems. Review changes before changing standards.
7. **Human control at boundaries.** The harness does not approve specs, independently approve PRs, or authorize PRD deployment.
8. **Security is not optional.** Command policies and credential boundaries must be enforced outside the agent's own instruction context; preserve failed/denied tool-call evidence.

## Proposed harness responsibilities

- Consume approved specifications and traceability metadata.
- Coordinate planning, implementation, testing, policy enforcement, and retry within budget.
- Produce evidence, a change set, and a reviewable PR package.
- Run deterministic checks and behavior/outcome evaluations.
- Record versions, costs/usage where available, failures, and uncertainty.

## Non-responsibilities

- Creating or approving company-wide principles without governance.
- Declaring a specification approved merely because an LLM generated it.
- Replacing independent PR review or production-release authorization.
- Treating reference project code as infallible or optimizing solely for one benchmark.
- Guaranteeing identical output across agents or promising that all software defects are detectable.

## Alternatives and tradeoffs

| Option | Tradeoff |
|---|---|
| Agent-specific conventions only | Simple but inconsistent across models and harder to evaluate. |
| Universal LLM-as-judge | Flexible but less reproducible for deterministic coding standards. |
| Deterministic checks exclusively | Objective but cannot measure all workflow behavior or business correctness. |
| Hybrid, independent checks (**proposed**) | Stronger evidence; requires more scenario and grader engineering. |

## Consequences

A reusable evaluation corpus and evidence contract become maintained engineering assets. Standards must be versioned and exceptions reviewed. Evaluation quality itself needs validation through known-good cases, deliberate violations, and holdouts. The harness will require isolated execution for untrusted generated code.

## Questions for ADR 0002 interview

1. Which company principles are mandatory **hard gates**, and which are recommendations?
   - **Answer:** All of them apply, but none are hard gates. Exceptions can be made with the right grounding.
2. Who can approve deviations/exceptions, and are exceptions per-story, per-repository, or time-limited?
   - **Answer:** Exceptions can be made at any level: the smallest owning authority decides, as long as it is documented.
3. Should the harness prescribe a fixed engineering workflow or allow agent choice as long as outcomes and evidence meet the contract?
   - **Answer:** The harness accepts any workflow; the described one is a means, not a mandate. Coding standards still apply.
4. Which steps may access live customer/cloud environments, and with what permissions?
   - **Answer:** Read-only only. Humans apply updates, creates and deletes.
5. Who maintains and approves the eval suite and benchmark holdouts?
   - **Answer:** The team (TeamValue/Bizure developers).
6. What evidence is mandatory for a PR to be considered review-ready?
   - **Answer:** When the requirements/acceptance criteria are proven by an automated test or other proof.
