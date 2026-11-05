# ADR 0001: Evolution of the Golden Path

- **Status:** Approved
- **Approved by:** teamvaluegroup, 2026-11-01T20:15:44Z
- **Date:** 2026-10-29
- **Decision owners:** Engineering leadership / Golden Path maintainers (to confirm)
- **Amended by:** ADR 0007 (prototype work, harness-repository review exception, local isolation)
- **Scope:** Company engineering way of working; agent-assisted software delivery
- **Supersedes:** None. Proposes amendments to the current Way-of-Work, not an immediate replacement.
- **References:** `Way-of-Work.pdf` (TeamValue/Bizure), ADR 0002, ADR 0003

## Context

The existing Golden Path defines how TeamValue/Bizure deliver business-critical applications. The process starts from a backlog item, proceeds through implementation and a pull request, and applies quality gates such as static analysis, linked work items, build validation, unit tests, and independent review. CI/CD promotes software through DEV, TEST, ACC, and PRD. The documented process automatically deploys to DEV but requires explicit approvals for TEST, ACC, and PRD.

The existing Way-of-Work is founded on **Segregation of Duties**, **Relentless Automation**, the **Four Eyes Principle**, **Traceability and Auditability**, and **Ownership**. It also places production approval with the Product Owner or delegate, subject to documented emergency exceptions. The process and its principles are not tied to a single DevOps platform, although the current document requires Azure Pipelines for deployments and permits limited GitHub use.

Agent-assisted development can accelerate delivery, but unconstrained adoption can amplify inconsistencies, conceal knowledge gaps, weaken testing, and make changes difficult to audit. The goal is to make a consistent, verifiable minimum engineering standard attainable across teams and experience levels, not to claim that an agent replaces senior engineering judgment.

## Decision

**Evolve the Golden Path into a human-controlled, agent-assisted SDLC.** Preserve the current governance principles while moving repetitive implementation, validation, and evidence collection into a reusable engineering harness.

1. **Backlog item remains the system of record.** A story/work item holds the approved specification or an explicitly versioned, linked specification artifact, acceptance criteria, rationale, and traceability links. The backlog is not replaced by a chatbot conversation or ephemeral agent context.
2. **Vegviser assists with knowledge and specification preparation.** It may use company knowledge and patterns to propose or refine a specification; it does not confer approval.
3. **Human acceptance sits between Vegviser and harness execution.** A human writes, reviews, or amends the specification in the story and expressly approves it before autonomous implementation begins.
4. **The harness implements the approved specification.** It orchestrates agent-assisted planning, implementation, tests, regression checks, policy compliance, and evidence collection. The agent may iteratively fix failing checks but may not weaken acceptance criteria or bypass controls.
5. **The team owns agent-produced work.** Named humans are still accountable for the story, PR review, and release decisions. Team ownership does not remove the requirement for a reviewer independent of the implementer/operator.
6. **Pull requests require human approval.** Automated checks supplement rather than replace independent review; post-approval code changes require reassessment under existing policy.
7. **DEV, TEST, and ACC promotion should become automated** when defined quality, functional, security, and environment-specific gates pass. This is a **proposed change** to the existing Way-of-Work, which currently requires explicit TEST and ACC approvals; it must be ratified before deployment policy is changed.
8. **PRD deployment continues to require an explicit manual approval** by the authorized Product Owner or delegate (including applicable emergency exceptions). After approval, the deployment itself should be automated.
9. **Regression acceptance is hybrid.** Approved business acceptance criteria are independent of the implementing agent and protected from unilateral modification. The agent may add unit, integration, and regression tests, but cannot redefine the approved business outcome to make its result pass.
10. **Traceability is mandatory:** story/specification version → execution record → code/commit → tests/evidence → PR/reviewer → build/release → production approval and deployment.

## Current Golden Path

```mermaid
flowchart TD
    A[Backlog item] --> B[Developer implements and tests]
    B --> C[Pull request linked to story]
    C --> D[Static analysis, build and tests]
    D --> E{Independent human PR review}
    E -->|Changes requested| B
    E -->|Approved| F[Merge and CI]
    F --> G[Automatic DEV deployment]
    G --> H{Manual TEST approval}
    H -->|Approved| I[Deploy and validate TEST]
    I --> J{Manual ACC approval}
    J -->|Approved| K[Deploy and validate ACC]
    K --> L{Manual PRD approval}
    L -->|Approved| M[Automated PRD deployment]
```

## Proposed Golden Path

```mermaid
flowchart TD
    A[Issue or work item: need, bug or improvement] --> B[Triage: clarify, prioritize and assign]
    B --> C[Vegviser-assisted specification and acceptance criteria]
    C --> D{Human approves specification?}
    D -->|Revise| C
    D -->|Approved and versioned| E[Harness: implement, test and verify]
    E --> F[PR linked to work item and evidence]
    F --> G{Quality gates and independent human review}
    G -->|Fix within scope| E
    G -->|Requirements change| C
    G -->|Approved| H[Merge and CI]
    H --> I[DEV → TEST → ACC with applicable gates]
    I --> J{Authorized human PRD approval}
    J -->|Approved| K[Automated PRD deployment]
    J -->|Not approved| L[Hold release]
    K --> M[Audit trail and operational feedback]
    M -.-> A
```

This diagram describes the intended process. Deployment permissions remain subject to the existing Way-of-Work and customer-specific gates. Automatic TEST/ACC promotion requires the policy agreement described in decision 7. The human specification checkpoint remains after Vegviser-assisted refinement and before harness execution.

### Detailed steps

1. **Record the request.** Create or link an issue or work item for a business need, bug, incident follow-up, or improvement. Capture the problem, rationale, available evidence, and affected system. Keep one canonical work item in the team's backlog tool, such as Azure Boards or GitHub Issues. Link related records rather than maintaining competing specifications.
2. **Triage the work.** Assess completeness, duplicates, affected components, and likely ownership. An agent can prepare this assessment and ask for missing information. A human decides priority, ownership, and whether to refine, defer, reject, or link the request to existing work. Record the disposition in the work item. Triage does not authorize implementation.
3. **Refine the specification.** Use Vegviser and repository context to draft the intended outcome, scope, acceptance criteria, nonfunctional requirements, constraints, and unresolved decisions. The human story owner writes or edits the result in the work item or a versioned artifact linked from it. Keep refinement proportionate to the change; a routine bug fix does not require a separate discovery exercise.
4. **Approve the specification.** Record explicit human approval against the specification version before autonomous implementation begins. Resolve decisions that materially affect scope or acceptance. A command invocation or board move alone does not establish approval.
5. **Implement and verify.** The harness consumes the approved version, plans and implements the change, generates tests, runs regressions and applicable checks, and collects evidence. It can fix failures within the approved scope. If the work requires changed requirements or acceptance criteria, return to refinement and obtain approval of the revised specification.
6. **Review the pull request.** Link the PR to the canonical work item, approved specification, and evidence. Deterministic quality gates, independent acceptance checks, and AI review support an independent human reviewer. Fix review findings within scope through the harness. Requirement changes return to refinement. Apply the existing reassessment policy when code changes after approval.
7. **Merge and promote.** After the required checks and human approval, merge and run CI. Deploy through DEV, TEST, and ACC under the applicable customer and environment policies. Automate promotion where policy permits it; retain required approvals where it does not.
8. **Authorize and deploy to production.** The authorized Product Owner or delegate approves the tested release/version for PRD. Hold the release when approval is withheld. After approval, the pipeline performs the deployment and records its result.
9. **Observe and feed back.** Verify the deployment and review operational feedback against the intended outcome. Link defects, incidents, and further improvements to new or existing work items for triage. Retain the trace from the approved requirement through implementation, review, and release.

### Boards and AI-assisted workflows

Azure Boards or GitHub Projects tracks progress across these steps; the board does not add another process stage. Use the team's existing statuses and link the work item, execution, PR, and release evidence. A merged PR does not by itself prove that a change has reached production or met its intended outcome. Apply the team's agreed closure criteria.

AI-first means agents prepare work by default where useful, while humans retain the decisions and approvals described above. Attach workflows to existing steps through events or explicit commands. Use automatic triggers for routine analysis and commands for deliberate requests or reruns. Commands request an operation; the workflow checks its prerequisites and the caller's authority before acting.

| Process step | Trigger or command | Expected assistance | Implementation status |
| --- | --- | --- | --- |
| Triage | New work item or `/golden-path-triage` | Assess completeness, duplicates, routing, and missing information; propose bounded metadata updates. | Proposed integration and command. |
| Specification | `/golden-path-refine` | Consult Vegviser and repository context; produce a draft specification, acceptance criteria, and open questions. | Proposed integration and command. |
| Implementation | Existing harness entry point | Consume the approved specification and produce implementation and verification evidence. | Harness responsibility already established; no new start command required by this refinement. |
| PR review | `/golden-path-review` | Review the change against engineering standards and the approved specification; report findings for human review. | Existing centralized workflow; see [ADR 0011](0011-centralized-agentic-review-workflow.md). |

Vegviser's MCP and the knowledge base behind it can provide context to triage, refinement, implementation, and review workflows. Start with read-only knowledge access and record the sources and revisions used where available. Validate authentication, runner connectivity, and tool permissions before enabling the integration. Vegviser continues to advise and produce drafts, consistent with [ADR 0003](0003-knowledge-to-code-boundary.md). Any automated backlog writes belong to an explicitly scoped workflow integration, not to Vegviser's specification authority.

Use the [GitHub Agentic Workflows gallery](https://github.github.com/gh-aw/gallery/) as a source of implementation patterns, particularly issue triage and PR review. Define permitted inputs, outputs, and writes for each workflow. Keep workflow logic centralized where appropriate, following ADR 0011. GitHub documents [custom MCP integration](https://github.github.com/gh-aw/reference/tools/#custom-mcp-servers-mcp-servers), [command triggers](https://github.github.com/gh-aw/reference/command-triggers/), and [safe outputs](https://github.github.com/gh-aw/reference/safe-outputs/). Azure DevOps work-item safe outputs are currently documented as experimental and require separate validation.

Introduce triage and refinement assistance first alongside the existing review command. Validate them on real work before expanding the command set. This adds assistance to the existing Golden Path without introducing additional human handoffs.

## Rationale

- **Speed:** remove repeated manual execution and handoffs when checks can produce reliable evidence.
- **Consistency:** apply the same company-defined conventions and architectural rules independent of agent, developer experience, or project.
- **Quality:** move verification earlier, require regression checks, and preserve independent review and release approval.
- **Knowledge transfer:** encode standards and examples in reusable, traceable mechanisms rather than relying solely on individual experience.
- **Control:** automate implementation and verification without granting the implementing agent authority over the business requirement or production release.

## Considered alternatives

| Alternative | Reason not selected |
| --- | --- |
| Retain the current manual process unchanged | Does not sufficiently address throughput, consistency, and reusable knowledge. |
| Let agents implement from unapproved prompts | Weakens requirement traceability and makes scope changes hard to audit. |
| Fully autonomous PR merge and production release | Conflicts with the current ownership, independent review, and PRD approval principles. |
| Treat generated tests as the only definition of correctness | Agents can validate their own misunderstandings; independent acceptance criteria are required. |

## Consequences and tradeoffs

**Positive**

- Engineers focus more on requirements, design judgments, reviews, and exceptions.
- Junior engineers can leverage an explicit, verified minimum standard while remaining accountable for understanding results.
- More complete links between intent, implementation, test evidence, and deployment.
- Faster promotion to TEST/ACC **if** automated gates prove trustworthy and policy changes are approved.

**Negative / risks**

- Quality becomes dependent on the clarity and review of stories/specifications.
- Agent-generated tests may encode the same mistaken assumptions as the implementation; independent business checks remain necessary.
- Harness policies can overconstrain valid solutions; exceptions and appeals require governance.
- Automated TEST/ACC promotion changes existing approval controls and needs explicit agreement from process owners.
- Human reviewers may experience review overload if evidence is noisy; reports should prioritize risk and explainability.
- Team ownership can blur individual responsibilities unless a responsible story owner, reviewer, and release approver are recorded.

## Implementation implications

- Extend backlog templates with specification, acceptance criteria, nonfunctional requirements, constraints, and links to evidence.
- Use a distinct human approval signal/versioned baseline before the harness can implement.
- Make the harness produce a structured PR evidence report: requirement mapping, test results, architecture checks, exceptions, and known uncertainties.
- Retain existing PR policies, build gates, static analysis, and deployment approval enforcement.
- Introduce TEST/ACC automatic promotion only after the Way-of-Work and relevant pipeline approvals are explicitly amended.
- Require appropriate credential and execution isolation for agent runs. For local work the read-only identity is the boundary, and sandboxing is an accepted risk (ADR 0007 decision 8).
- There is no prototype mode. Agent-written code in a project repository is production code. Useful exploration done elsewhere starts again at the approved-spec step (ADR 0007 decision 7).
- The independent-review requirement (item 5) applies to product repositories. The harness repository has a documented exception while it has a single maintainer (ADR 0007 decision 2).
- Define measurable indicators: cycle time, escaped defects, regression detection, review effort, compliance drift, and traceability coverage.

## Implementation questions and rollout checks

1. Who is the accountable story owner within the collectively owning team, and how is that recorded?
   - **Answer:** Business and developer together, who give the commitment. Recorded in the backlog tool in use (Azure DevOps, GitHub Issues or Jira).
2. Which objective gates are mandatory before automatic TEST/ACC promotion, and who may grant exceptions?
   - **Answer:** Depends on the customer: TEST and ACC may or may not be gated. DEV is for the developers and is not gated.
3. What constitutes a versioned, human-approved specification in Azure Boards / future GitHub workflows?
   - **Answer:** The specification is registered in the backlog tool and the docs in the repo are kept up to date. The combination keeps decisions traceable through time.
4. Does company policy permit exceptional self-review/hotfix procedures to continue unchanged for agent-authored changes?
   - **Answer:** No. A human always stays in control for PRD.
5. How are acceptance tests independently maintained when requirements change after harness execution begins?
   - **Answer:** Acceptance tests live in a separate repo. When requirements change, the regression/acceptance scenarios change with them.

## Decision review triggers

Revisit this ADR after the first greenfield and multiple brownfield evaluations, after a production incident attributable to the agentic workflow, or before relaxing any human approval control.
