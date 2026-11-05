---
name: acceptance
description: Prepare business test plans, user acceptance matrices, and executable test sheets for stakeholder sign-off. Use when creating acceptance plans or preparing for business verification. Do not use for automated unit or integration tests.
---

# Business Acceptance Discipline

Translate feature specifications into executable business test sheets for user and stakeholder acceptance.

## Triggers & Scope
- **Use when**: Preparing acceptance criteria for business sign-off, UAT sessions, or release qualification.
- **Skip when**: Writing developer-facing unit or integration test code.

## Core Rules
1. **User language**: Frame test scenarios in the vocabulary of business users, not internal code mechanisms.
2. **Executable & falsifiable**: Each test sheet step has clear preconditions, actions, and expected business outcomes.
3. **Human sign-off**: The agent prepares the test sheet and records results; business stakeholders accept the release.

## Process & Tooling
Follow the canonical playbook: [write-business-test-plan.md](~/.golden-path-harness/harness/playbooks/write-business-test-plan.md).

1. Generate the test plan workbook:
   `tvh testing business-plan <plan-spec.json> business-test-plan.xlsx`
2. Align test rows with approved spec criteria from `specs/<slug>.md`.

## Expected Evidence
An executable business test plan workbook (`business-test-plan.xlsx`) linking to approved specifications.
