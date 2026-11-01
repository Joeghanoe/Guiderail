# ADR 0004: Harness Scope and Boundaries

- **Status:** Draft — requires team review
- **Date:** 2026-10-29
- **Scope:** Responsibilities, ownership, interfaces, and intentional exclusions of the Golden Path Harness
- **Depends on:** ADR 0001, ADR 0002, ADR 0003
- **Amended by:** ADR 0007 (harness owner, no prototype mode, sandboxing as accepted risk)

## Context

The Golden Path is evolving toward a human-controlled, agent-assisted development process. Without explicit boundaries, the harness could become a replacement backlog, specification authority, CI/CD platform, deployment approver, or knowledge base. That would weaken accountability and introduce unnecessary overlap. ADR 0001 establishes human approval of backlog specifications, independent PR review, and human PRD approval. ADR 0003 proposes Vegviser as a knowledge/specification assistant, with the approved backlog story as the source of truth.

## Proposed decision (not yet ratified)

**The harness is a controlled engineering execution and evidence-generation layer, not a decision authority.**

### In scope

1. Consume an explicitly approved and versioned backlog story or a linked immutable specification artifact.
2. Orchestrate planning, implementation, test creation, validation, bounded remediation and preparation of a reviewable pull request.
3. Apply company engineering principles through agent instructions, deterministic checks, permissions and suitable behavioral evaluations.
4. Integrate with existing source control, project tooling, build and delivery interfaces rather than replacing them.
5. Produce traceable artifacts: changes, tests, execution traces, findings, exceptions, and evidence linked to the story and commit.
6. Support greenfield and brownfield work, including identification of inherited versus newly introduced violations.
7. Support interchangeable agent/model adapters while maintaining a common scenario and evidence contract.
8. Treat every piece of agent-written code in a project repository as production code. There is no relaxed prototype mode (ADR 0007 decision 7).

### Out of scope

1. Become the authoritative store of business requirements, company knowledge, or approval state.
2. Approve or silently revise specifications, company standards, PRs, or production releases.
3. Replace the CI/CD system, the backlog system, SonarCloud, or organizational governance as a matter of principle.
4. Grant itself elevated privileges or bypass command and credential restrictions.
5. Guarantee correctness solely because generated tests pass; independent acceptance evidence remains necessary.
6. Turn every existing codebase discrepancy into mandatory refactoring unrelated to the approved story.

## Ownership and control boundaries

| Boundary | Accountable owner | Harness role |
| --- | --- | --- |
| Company architectural principles | Designated company governance owner (to confirm) | Apply approved, versioned rules |
| Business specification | Human story owner / authorized approver (role to confirm) | Read approved specification |
| Implementation quality | Delivery team | Generate and verify evidence |
| PR acceptance | Independent human reviewer | Prepare PR and evidence, never approve |
| TEST/ACC promotion | Pipeline with approved environment gates, **subject to company policy ratification** | Supply evidence; not unilaterally change deployment policy |
| Production release | Product Owner or authorized delegate | Never authorize approval |
| Evaluation suite | joeghanoe, independent from the candidate run (ADR 0007) | Execute trusted evaluators |
| Harness rules, examples, gates and their review | joeghanoe, owner and reviewer; a documented exception to segregation of duties for this repository only (ADR 0007 decision 2) | Apply the versioned harness; never edit it during a run (H.1) |

## Options considered

| Option | Assessment |
| --- | --- |
| All-in-one AI delivery platform | Appears convenient but duplicates systems of record and concentrates authority |
| IDE-only prompt/skills collection | Lightweight, but inconsistent enforcement, weak auditability and little repeatability |
| Bounded orchestration and evidence layer (**proposed**) | Clear accountability and portability, but requires well-defined integration contracts |

## Consequences and tradeoffs

- Favors existing organizational process and traceability over maximal autonomy.
- Introduces integration work and a stricter contract for story approval and evidence.
- Human review remains a throughput constraint by design.
- Internal folder layout and installation under `~/.golden-path-harness` are implementation details; they must not redefine the responsibility boundary.
- This ADR does **not** itself authorize changes to existing environment approval policies.
- **Accepted risk (ADR 0007 decision 8):** day-to-day local agent work is not sandboxed. The hooks are a guardrail, and the read-only cloud identity is the boundary. Benchmark runs use a container. Revisit this when the harness is used on untrusted repositories.

## Open questions

1. Which role is permitted to approve a story for autonomous implementation?
   - **Answer:** Developer, Architect.
2. May the harness create backlog subtasks or PR drafts, and under what identity?
   - **Answer:** No: the human stays in control of the backlog. An agent may create a PR, always in agreement with the user.
3. Should it ever deploy to ephemeral developer environments, or only prepare assets for existing pipelines?
   - **Answer:** If a dev pipeline exists, deploying to DEV is wise. A containerised environment may be simulated locally, but the result must always be validated on live infrastructure.
4. Who owns policy exemptions and how are they time-bounded and audited?
   - **Answer:** Architects can grant exemptions. They must be documented in the repo.
5. What is the supported scope beyond software (infrastructure, databases, operations)?
   - **Answer:** Software, infrastructure, databases and operations; no more than these four.

## Acceptance criteria for ratification

- A reviewed responsibility matrix names systems of record, approving roles and harness permissions.
- A demonstration shows an agent cannot approve its own spec/PR/PRD release.
- The harness can explain which standards, tests and approvals apply to a story without redefining them.
