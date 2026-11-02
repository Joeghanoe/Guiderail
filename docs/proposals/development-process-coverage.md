# Proposal: close gaps in development and process coverage

Status: discussion draft for colleague interviews. No new rules, roles, approval gates, or implementation commitments are approved by this proposal.

Date: 2026-11-01

## Recommendation

Extend our assessment of the harness beyond whether it helps us implement a change correctly. Assess whether our wider development process helps us choose the right change, understand its effects, operate it safely, and establish whether it achieved its purpose.

Start with colleague interviews using recent work as evidence. Confirm which gaps cause actual problems, who owns each capability, and whether the answer belongs in the harness, Vegviser, a product repository, existing tooling, or a human workflow. Build the smallest useful support for the highest-impact gaps.

The proposal covers every area currently assessed as partial or thin, and the remaining weaknesses inside areas assessed as good. These assessments describe available guidance and tooling. They are not measured success rates or findings about colleagues' competence.

## Current position

The repository has substantial support for implementation, code review, test discipline, IaC conventions, pipeline investigation, and operational investigation. Examples include design-first scaffolding, scenario requirements, generated API contract checks, frontend screenshots and accessibility checks, read-only operational tools, and evidence-linked review findings.

Coverage is uneven across the lifecycle and technology stacks. A documented principle, a playbook, an automated check, and a demonstrated capability provide different levels of confidence. Some workflows remain drafts or depend on project-specific integration.

The assessment is based on the [rules](../../harness/rules/index.md), [playbooks](../../harness/playbooks/index.md), [tools](../../harness/tools/index.md), [gates](../../harness/gates/index.md), and [evaluation structure](../../benchmarks/cases/README.md). Interviews should test the assessment against actual use.

## Process review before specification

Introduce a process review capability before detailed specification when a request changes a business process, crosses ownership boundaries, or leaves the underlying problem unclear. “Process reviewer” names a responsibility to investigate, not a proposed new job title or mandatory agent.

The current spec workflow helps turn a stated requirement into checkable acceptance criteria. It does not establish that the requested change addresses the right business problem. A precise spec can still automate an unnecessary step, move a bottleneck elsewhere, or optimise one team's work at another team's expense.

The process reviewer should establish:

- Which end-to-end process contains the request, what triggers it, and where it ends.
- Who performs the work, who receives the result, and who owns the process and its exceptions.
- Which problem occurs today, how often it occurs, and what evidence supports the claim.
- Which business rules, handovers, systems, and dependencies constrain the change.
- Whether software is the appropriate intervention, compared with removing a step, changing a policy, clarifying ownership, or using an existing capability.
- What outcome should improve, how we will observe it, and what must not get worse elsewhere.

The output should be a short process context note containing the problem, current process, affected roles and systems, evidence, options, expected outcome, assumptions, and unresolved decisions. A diagram is useful when handovers or exceptions make prose hard to follow. Do not require a modelling notation for every request.

For example, a request to “add automatic reminders for unprocessed requests” might be valid. It might also conceal unclear ownership or an intake queue nobody monitors. The review should establish which problem exists before we specify the reminder implementation.

The proposed sequence is business need, proportionate process review, human agreement on the problem and intended outcome, specification, implementation and verification, release, then outcome review. Small changes with an established process can reuse existing context. Technical maintenance work can record why a separate business process review adds no value.

The trade-off is extra investigation before implementation. It is justified when it prevents building the wrong change. It becomes waste if every routine fix requires a full discovery exercise.

## Gaps to validate

“Good with gaps” means useful support exists, but the remaining gap still belongs in this proposal. Suggested support is a discussion option, not an agreed solution.

| Capability | Current assessment | Gap to investigate | Possible support |
| --- | --- | --- | --- |
| Business process analysis | Partial | We can formalise a request without establishing where it belongs in the process or whether it solves the underlying problem. | Process review, current and proposed process, handover and exception analysis, named process owner. |
| Requirements and business rules | Partial | Specs and acceptance criteria exist, but stakeholder discovery, conflicting requirements, terminology, and business-rule analysis have little structured support. | Stakeholder questions, glossary, decision tables, ambiguity review, requirement provenance. |
| Product discovery and prioritisation | Thin | Limited support for comparing opportunities, testing assumptions, deciding what not to build, and reviewing benefits after delivery. | Outcome hypotheses, lightweight option comparison, success measures, post-release outcome review. |
| UX and interaction design | Partial | Visual and responsive checks do not establish that people can understand and complete their tasks. | Journey and task analysis, information architecture review, interaction-state review, usability sessions. |
| Accessibility assurance | Partial | Automated checks cover only part of accessibility; manual keyboard, assistive technology, and real-device checks need clearer ownership and evidence. | Risk-based manual checklist and accessible interaction acceptance criteria. |
| Frontend architecture | Good with gaps | Less dedicated support for state ownership, data fetching, routing, component boundaries, and consistent interaction states. | Repo-specific conventions and review examples for loading, empty, error, permission, and concurrent-update states. |
| Backend and stack breadth | Good with gaps | Much of the concrete structural enforcement is .NET-oriented. Equivalent support across other stacks and application types is not established. | Identify supported stacks, map equivalent checks, and evaluate representative changes before claiming parity. |
| API and integration lifecycle | Good with gaps | Contract generation and adapter tests do not fully cover compatibility, versioning, consumer impact, deprecation, or event-schema evolution. | Compatibility checks, consumer inventory, contract tests, deprecation and integration-change review. |
| Database and schema changes | Thin | No dedicated workflow for migration safety, mixed-version compatibility, backfills, concurrency, or recovery after a failed change. | Migration review, rollout sequence, representative-data verification, explicit recovery procedure. |
| Data quality and governance | Thin | Design templates address layout and retention, but data ownership, lineage, quality rules, reconciliation, and deletion verification need more support. | Data contracts, ownership records, reconciliation checks, retention and deletion evidence. |
| Security assurance | Partial | Identity and secret-handling rules do not establish complete application security, especially authorisation and tenant isolation. | Proportionate threat modelling, abuse cases, authorisation tests, vulnerability triage and remediation workflow. |
| Privacy and compliance | Partial | Keeping personal data out of logs and prompts is narrower than assessing permitted collection, use, access, retention, and deletion. | Data-flow review and referral to accountable privacy or compliance owners when required. |
| Performance and capacity | Partial | Algorithm sizing and design expectations exist, but representative load testing, latency budgets, capacity limits, and bottleneck diagnosis are less developed. | Workload profiles, targeted load tests, performance budgets, profiling workflow. |
| Reliability and disaster recovery | Partial | Health, telemetry, and failure models do not prove that a service tolerates dependency failure or can recover its data and operation. | SLOs, failure exercises, backup restore tests, agreed recovery objectives and recovery drills. |
| Infrastructure lifecycle | Good with gaps | IaC gates detect selected explicit settings. They do not establish safe effective configuration, drift control, resource lifecycle, or resilient topology. | Effective-configuration validation, plan review, drift investigation, infrastructure readiness checks. |
| Delivery and release management | Good with gaps | Pipeline support is strongest in Azure DevOps. Deployment compatibility, progressive rollout, recovery, and equivalent integration elsewhere need validation. | Release-risk review, rollout and recovery plans, evidence contracts for other CI platforms. |
| Operational readiness and service ownership | Partial | Investigation tools exist, but ownership, support handover, actionable runbooks, and readiness to operate need a more explicit workflow. | Named service owner, support expectations, tested runbooks, proportionate readiness review. |
| Incident management and learning | Partial | Technical triage is better supported than incident coordination, escalation, stakeholder communication, postmortems, and follow-up verification. | Incident role guidance, timeline and postmortem templates, tracked corrective actions. |
| Test strategy and acceptance | Strong foundation with gaps | Layered tests and scenario presence do not prove that assertions are meaningful, all material risks are covered, or business acceptance is independent of implementation assumptions. | Risk-based test review, independent acceptance evidence, exploratory testing, representative test data. |
| Architecture across services | Good with gaps | Service design support is stronger than cross-service dependency review, brownfield evolution, and tracking whether architectural assumptions remain true. | Dependency and impact review, incremental migration plans, follow-up on consequential decisions. |
| Cost and resource efficiency | Partial | Run cost measurement exists, but application infrastructure cost, demand forecasts, and the cost consequences of design choices need explicit attention. | Cost assumptions in design, usage review, targeted cost investigation. |
| Harness adoption and effectiveness | Good with gaps | Tooling and evaluations exist, but reliable outcomes across roles, stacks, adapters, and real projects require evidence. | Capability-level evaluations, adapter verification, sampled real-work reviews, onboarding feedback. |

## Boundaries and ownership

Keep the harness focused on engineering execution and evidence. Business discovery support may belong in Vegviser or an existing business analysis workflow. The harness can consume the resulting context and identify missing information without becoming the authority on business priorities.

The proposed boundary is consistent with the direction in [ADR 0003](../adr/0003-knowledge-to-code-boundary.md) and [ADR 0004](../adr/0004-harness-scope-and-boundaries.md), both of which still describe draft governance decisions. Interviews should confirm ownership rather than treat those drafts as settled company policy.

Humans decide business outcomes, approve specifications, accept risk, and authorise releases. Agents can gather evidence, expose contradictions, compare options, and prepare artifacts. A process reviewer must not invent an intended outcome or approve its own recommendation.

Prefer existing tools and workflows when they already solve the problem. A gap in this repository may indicate a missing integration or documentation link rather than missing organisational capability.

## Colleague interview guide

Interview people involved in process ownership, business analysis, product decisions, UX, development, testing, architecture, security, data, platform engineering, and support. One person may cover several responsibilities. Start with a recent change or incident rather than asking only for opinions about the proposed capabilities.

1. Describe a recent change that was technically correct but failed to solve the intended problem. When could we have recognised that?
2. How do you establish where a request fits in the end-to-end process? Who checks effects on other teams and exception paths?
3. What information is usually missing when work reaches specification or development? Who can supply or decide it?
4. Which business rules or acceptance criteria are repeatedly misunderstood? Show an example if possible.
5. Which capability gaps in the table have caused rework, incidents, delay, or avoidable cost? Which are already handled well elsewhere?
6. What existing artifact, tool, or review should we reuse? Where does the current handover fail?
7. What could an agent usefully prepare or verify? Which judgment must remain with a named person?
8. What is the smallest useful intervention? When should it apply, and when should we skip it?
9. What evidence would convince you that the intervention works? What would make it too burdensome?
10. Which two gaps would you address first, and who would help test the proposed support on real work?

Use targeted follow-ups for each interviewee's responsibilities. For example, ask a database specialist to walk through a failed migration and recovery, or ask support to show a runbook they could not use during an incident.

### Interview record

Keep customer details, credentials, personal data, and private operational evidence outside this public proposal. Record sanitised findings here only when appropriate.

| Field | Capture |
| --- | --- |
| Responsibility represented | Role or discipline; personal attribution only with agreement. |
| Capability and example | The gap discussed and a concrete recent situation. |
| Current handling | Existing owner, workflow, tool, and artifact. |
| Consequence | Rework, delay, risk, user impact, or cost; distinguish observation from estimate. |
| Proposed intervention | Smallest useful change, including trigger and owner. |
| Placement | Harness, Vegviser, product repo, existing tool, or human workflow. |
| Confidence | Confirmed by evidence, reported experience, or untested hypothesis. |
| Priority and next step | Reason for priority, open decision, and candidate pilot. |

## Prioritisation and pilot

Do not convert every row into a mandatory gate. Prioritise confirmed gaps by consequence, recurrence, current alternatives, implementation effort, and ongoing process cost. Record disagreements instead of averaging away different responsibilities' needs.

Initial candidates are process review before specification, database change safety, security assurance, and operational readiness. This ordering is a starting hypothesis for interviews, not a delivery commitment. Move other gaps ahead when the evidence supports it.

For each selected gap:

1. Name an owner and a concrete failure the intervention should prevent.
2. Define its trigger, required inputs, useful output, and human decision boundary.
3. Pilot a short checklist or playbook on representative real work, including a case where it should not apply.
4. Assess whether it exposed a material omission, changed a decision, reduced rework, or improved verification. Record time spent and false alarms as well.
5. Automate stable, checkable parts after the pilot shows value. Evaluate the resulting capability independently of whether the agent completed the checklist.

For process review, success includes recognising when a software change is unnecessary or when more evidence is needed. Producing a spec is not itself a success measure.

## Decisions after interviews

The interview synthesis should identify confirmed gaps, existing capabilities we should reuse, disputed assumptions, and work we deliberately defer. It should propose the first pilots with owners, expected benefits, effort, and evidence of success.

The immediate decision is which capabilities to pilot and where they belong. Adopting new company standards, mandatory gates, or approval responsibilities requires a separate explicit decision.
