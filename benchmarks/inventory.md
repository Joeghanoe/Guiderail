# Evaluation inventory

Inventory of this checkout, 2026-10-29. This is an assessment, not approval of new standards or scoring.

## Existing architecture

- `harness/index.md` organizes principles, rules, examples, playbooks, gates, tools and Claude hooks. It identifies Vegviser as the authority for principles. `harness/principles/` contains pointers, not proof that the complete authoritative source was reviewed.
- `AGENTS.base.md`, adapters and `install.sh` provide agent-facing integration; `harness/hooks/guard-bash.sh` and `guard-read.sh` are Claude hooks. The Bash guard explicitly describes itself as a guardrail, not a sandbox; equivalent enforcement for other agents is not established.
- `harness/tools/review/eval.py` creates disposable repositories and scores reviewer findings against examples; `eval-queue.py` resumes runs. Claude and Copilot adapters exist. This is a reviewer evaluation, not an implementation-agent SDLC runner. Its example masking does not establish a separate held-out dataset.
- `harness/gates/` registers existing deterministic checks, including IaC, scenario presence, framework currency and banned APIs. `tests/run.sh` exercises hooks and tools, including a sizeable command allow/deny matrix. `azure-pipelines.yml` runs bundle, privacy, test and shell checks and conditional reviewer evals. Reviewer outputs are published by CI; raw outputs are excluded from the checkout.
- `harness/tools/orchestration/` recommends model tiers; it is not evidence of equivalent benchmark execution or cost accounting.

## Inputs and gaps

- The imported global instructions point to `C:\Users\Verst\source\repos\werk\files\TeamValue Principles & Context\`; that path is inaccessible on this machine. The harness points to Vegviser as authority. Its completeness and currency have not been verified.
- The two reference locations were subsequently supplied as `D:/Prototypes/TV/Bizure.Backups` and `D:/Prototypes/TV/TeamValue.IntegrationHub.*` (moved under TV). The remaining project corpus, calibration/holdout allocation, business specification and functional acceptance criteria have not been identified. Do not infer them from examples or local directories.
- `harness/rules/code/code-5-one-responsibility.md` is human-verified and references P-02, with a private nested-type exception and touched-file boundary. It is currently enforced by review. The user subsequently approved the C# structural scope and fixture criteria; an explicit checker is now implemented under `harness/tools/code/`, with CI integration still open.
- No implementation-agent runner, independent frozen grader, inherited-violation baseline, holdout controls, comparable execution budget or complete cost/trace reporting has been established by this inventory. Existing reviewer examples should not be presented as evidence of these capabilities.

## Smallest integration plan

1. Obtain the authoritative principles and both references; compare evidence to the existing rule catalog and record conflicts and candidate exceptions for human review. Preserve stable rule IDs and existing metadata; add traceability only where evidence supports it.
2. Agree on the exact scope, exceptions and approval of one deterministic rule and its evaluation criteria. Extend an existing gate/tool pattern, with fixtures and independent tests, rather than changing policy or thresholds silently. For C# type declarations use a syntax-aware implementation; distinguish partial types, nested types and generated files explicitly.
3. Extend existing example/evaluator machinery only where it fits; keep graders and policy outside the evaluated agent's write scope, capture evidence and distinguish policy hard gates from quality outcomes. Test bypasses without assuming the hook is a security boundary.
4. After the missing specifications and project assignments are supplied, design isolated implementation scenarios and frozen acceptance criteria, separating inherited violations and protecting holdouts. Do not claim generalization or benchmark fairness before those runs exist.

## Approval status

The user approved the guidance decisions, CODE.5 structural scope and evaluation criteria on 2026-10-29.
See [Engineering standards and accepted decisions](engineering-standards-decisions.md) for current status
and remaining implementation work. Future changes to principles, exceptions, criteria or policy still
follow the human-review requirement in the implementation brief.

Update 2026-10-29: Six principle Loop pages were supplied as exports, along with the two project paths. See engineering-standards-decisions.md for preliminary classification, project observations and unresolved conflicts. Both top-level project paths lack Git metadata; immutable revisions remain to be identified.
