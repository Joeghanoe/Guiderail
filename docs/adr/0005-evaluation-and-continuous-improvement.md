# ADR 0005: Evaluation and Continuous Improvement

- **Status:** Draft — requires team review
- **Date:** 2026-10-29
- **Scope:** Benchmark lifecycle, evaluation ownership, continuous improvement and evidence
- **Depends on:** ADR 0001, ADR 0002, ADR 0004

## Context

The harness must make company engineering principles measurable, rather than relying on instructions or a model's claims. Two reference repositories provide candidate conventions; approximately 8–10 existing projects offer audit and evaluation material. The intended sequence is to distill standards, test a greenfield business case, then introduce brownfield projects one at a time. Existing projects are not automatically compliant or exemplary. A benchmark optimized against a single example can overfit and lose generality.

## Proposed decision (not yet ratified)

**Maintain a versioned, independent evaluation system with a controlled improvement loop.** Separate tests of the harness itself from evaluation of agent-generated work.

### Evaluation types

| Type | Evaluates | Preferred mechanism |
|---|---|---|
| Harness unit/integration tests | Whether harness code, policy scripts and runners behave correctly | Conventional automated tests |
| Deterministic conventions | Class/file structure, formatting, compilation, static analysis, tests | Parsers, analyzers and executable assertions |
| Security/tool policy | Allowed and prohibited actions | Deny/allow matrices plus independent execution enforcement |
| Behavioral evals | Tool choices, remediation, truthful reporting, respect for denials | Captured traces with explicit rubric |
| Functional outcome evals | Approved business acceptance criteria | Independent acceptance tests and observable artifacts |
| Qualitative review | Architecture fitness and maintainability requiring judgment | Calibrated review rubric; human review as needed |

### Lifecycle

1. **Distill standards:** Map company principles to scoped, versioned, observable rules; label legitimate exceptions. Use reference repositories as evidence, not truth.
2. **Calibrate evaluators:** Test known-good implementations, deliberate violations, and false-positive cases before trusting scores.
3. **Greenfield baseline:** Start from a clean project and an approved spec; allow the agent to design and implement within policy. Grade functionality and architecture separately.
4. **Brownfield validation ladder:** Audit each project's existing compliance, then run scoped work tasks. Separate inherited violations from introduced regressions.
5. **Diagnose disagreements:** Classify project defect, evaluator defect, incomplete principle/exception, model/harness failure, or insufficient evidence.
6. **Review improvements:** Propose rule or harness changes with a rationale; keep them out of the candidate's control during a run. Rerun known regressions and unseen validation cases.
7. **Publish reproducible results:** Pin scenario, starting commit, standards, evaluator version, model/adapter/harness revision, runtime and evidence.

### Scoring and safeguards

- Functional correctness, architectural compliance, behavioral compliance and command-policy compliance are separate result dimensions.
- Hard-gate violations cannot be offset by a favorable aggregate score.
- `inconclusive` and `not applicable` are valid outcomes when evidence is insufficient or a rule does not apply.
- The candidate agent must not change hidden grader definitions, approved acceptance criteria, or scoring thresholds during its run.
- Keep a holdout of projects/scenarios unseen during tuning; avoid using a holdout's results to iteratively optimize and then claiming it remains unseen.
- Preserve run artifacts so grading changes can be replayed **without rerunning a paid model**, where the evaluator supports replay.
- For model comparisons, use repeated scenarios when feasible and report success rates, hard-gate failures, latency, total usage and cost per successful outcome (measured or explicitly estimated).

## Alternatives considered

| Option | Assessment |
|---|---|
| Rely on prompt adherence alone | Does not verify actual behavior or outcomes |
| Single LLM judge and overall score | Flexible but weaker reproducibility and hides critical failures |
| One golden project and exact-output matching | Simple but high risk of overfitting and rejecting valid alternative solutions |
| Independent, mixed-method evaluations (**proposed**) | More work, but more reliable and auditable evidence |

## Consequences

- Evaluation rules, fixtures, approved exceptions and benchmark results become governed engineering assets.
- Some judgments will remain manual or inconclusive; avoid false precision.
- Repeated agent runs consume subscription quotas or API budget, so initial evaluation should be sequential and prioritize evidence replay.
- Evaluators that execute untrusted code require isolation; the executing agent should not see private reference implementations.

## Open questions

1. Who can approve a new rule or change an existing rule's severity?
2. What minimum evidence constitutes a review-ready PR?
3. Which scenarios form calibration, regression and holdout sets?
4. Which compliance rules are hard gates, advisory warnings or legitimately project-specific?
5. What constitutes a meaningful improvement: pass rate, review time, reliability, cost, or all of these?
6. How are false positives, rule disagreements and emergency exceptions reported?

## Acceptance criteria for ratification

- Each active rule maps to an approved principle or explicitly reviewed convention.
- A known-good and deliberately violating fixture demonstrate evaluator sensitivity.
- Greenfield and brownfield reports distinguish functional outcomes, inherited debt and introduced defects.
- A failed candidate cannot edit its grader to make the run pass.
- The suite can be replayed and versioned for later cross-model comparisons.
