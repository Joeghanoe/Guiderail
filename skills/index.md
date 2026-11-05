# Engineering processes

The [process catalog](processes.json) maps current and future coverage. Select the step appropriate to the request; this is not a mandatory lifecycle or a chain of skill invocations. Pass artifacts, criterion identifiers and open questions between steps rather than the full conversation.

| Step | Skill | Status | Owner | Inputs | Outputs or gap |
| --- | --- | --- | --- | --- | --- |
| understand-work | Not installed | planned | Business/process owner with Vegviser | request and affected process | agreed outcome, rules and accountable owner. Gap: Agree analysis procedure with the process owner |
| research | Not installed | planned | Architecture owner | bounded question and source constraints | source-grounded conclusion and uncertainty. Gap: Define research evidence and stopping conditions |
| specify | [specify](engineering/specify/SKILL.md) | active | Requester / product owner | request, source work item and existing criteria | provenance, criteria, questions and agreement status |
| design | [design](engineering/design/SKILL.md) | active | Architecture owner / existing ADR authority | criteria, current architecture and constraints | design, trade-offs, interfaces and open decisions |
| plan | [plan](engineering/plan/SKILL.md) | active | Engineering lead | approved criteria, design and source scope | bounded packages, dependencies and verification commands |
| implement | [implement](engineering/implement/SKILL.md) | active | Change author | approved criteria, source scope and plan when needed | focused diff and criteria-to-evidence mapping |
| test | [test](engineering/test/SKILL.md) | active | Change author / test owner | criteria or reproduced defect and public test boundary | tests, scenario mapping, results and gaps |
| debug | [debug](engineering/debug/SKILL.md) | active | Engineering / incident owner | observed failure, version, environment and logs | diagnosis, confidence, reproduction and bounded next action |
| verify | [verify](engineering/verify/SKILL.md) | active | Engineering / environment owner | source or deployed version and required checks | receipts, failures, skips and residual judgment |
| code-review | [code-review](engineering/code-review/SKILL.md) | active | Independent reviewer; human merge authority | baseline, source scope, criteria and check evidence | standards and spec assessment, validated findings and unresolved decisions |
| acceptance | [acceptance](engineering/acceptance/SKILL.md) | active | Business owner | approved criteria, environment and business process | runnable test plan and recorded evidence for human acceptance |
| prepare-delivery | Not installed | planned | Release owner / product owner | review, current receipts and compatibility scope | readiness, rollout and recovery plan. Gap: Agree release-readiness procedure; no publishing authority is granted |
| verify-operation | [verify](engineering/verify/SKILL.md) | active | Environment / service owner | deployed version, environment and observation window | version, health and telemetry observations |
| learn | Not installed | planned | Incident owner / harness maintainer | incident evidence and feedback | postmortem, follow-up actions and revalidation. Gap: Shared feedback exists; agree incident-learning ownership and procedure |
| improve | Not installed | planned | Architecture / process owner | observed outcomes and maintenance costs | bounded improvement decision and evaluation. Gap: Agree effectiveness measures before mandatory process changes |

Shared procedures remain in [playbooks](../harness/playbooks/index.md). Review and business acceptance procedures live beside their owning skills; design, implementation, test and debugging details load conditionally from flat supporting files. Security, compatibility, migrations, privacy, performance, recovery and UX remain conditional concerns under the [coverage assessment](../docs/proposals/development-process-coverage.md). A missing organizational decision remains a visible planned gap.

Native installation currently targets Claude Code and Copilot. Codex parity is unassessed. A source or installed-link check establishes packaging, not actual model selection or successful workflow completion.
