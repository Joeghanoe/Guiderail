---
name: verify
description: Verify code, frontend UI, or deployments against quality gates before calling work complete. Use when preparing to finish a task, checking visual/accessibility regressions, or validating a deployed service. Do not use for code review or debugging.
---

# Verification Discipline

Execute mandatory quality and safety gates before declaring work complete.

## Triggers & Scope
- **Use when**: Finishing a code change, checking frontend UI / accessibility, or verifying that a deployment is healthy.
- **Skip when**: In the middle of exploratory prototyping or when code review is requested.

## Core Rules
1. **Never assume success**: Missing tools, failed checks, or timeouts are incomplete runs, never clean passes.
2. **Honest reporting**: Report exactly what ran, what failed with its output, and what was skipped with a clear reason.
3. **Segregation of duties (CLD.2)**: Verification confirms status; it does not authorize promotion to PRD.

## Process & Tooling
Follow the relevant verification playbooks:
- **Project code gate**:
  `tvh verify --repo .`
- **Frontend UI & accessibility (UI.1/UI.2)**: [verify-frontend.md](~/.golden-path-harness/harness/playbooks/verify-frontend.md)
  Check contrast: `tvh frontend contrast --css <file> --pair <fg>/<bg>`
  Capture screenshot: `tvh frontend capture --url <url>`
  Compare UI: `tvh frontend compare --baseline <base.png> --current <curr.png>`
- **Deployment health**: [verify-deployment.md](~/.golden-path-harness/harness/playbooks/verify-deployment.md)
  `tvh cloud read az rest --method get --url <health-url>`

## Expected Evidence
Retained verification receipts (`result.json`), visual diffs (if UI), or health status reports with zero unhandled failures.
