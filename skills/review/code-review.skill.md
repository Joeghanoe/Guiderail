---
name: code-review
description: TeamValue code review process, severity model, and verdict format. Use when reviewing a diff, pull request, or change. Delegates the substance to the canonical principle and security files.
---

Use this skill to review a change before merge. Review the diff only — do not rewrite the author's code. Produce findings and a verdict.

This skill owns only what is review-specific: the process, severity model, verdict format, and rules. **The substance of what to check lives in the canonical files below — read them, do not duplicate them.**

## Sources of truth (read these to judge findings)

| What to check | Canonical source |
|-|-|
| Architectural principles (`A.1`–`A.20`) | `instructions/principles.instructions.md` |
| Global engineering & security defaults (secrets, identity, TLS, logging, comments) | `instructions/global.instructions.md` |
| Backend security (authN/Z, input validation, injection, error handling) | `skills/backend/production/security.skill.md` |
| Backend correctness, observability, resilience, async | `skills/backend/production/*.skill.md`, `skills/backend/core/*.skill.md` |
| Frontend security & review checklist (`S.3`, `S.6`, POLA) | `skills/frontend/frontend-security-and-review.skill.md` |
| Frontend architecture & state | `skills/frontend/frontend-architecture.skill.md`, `skills/frontend/frontend-state-and-data.skill.md` |
| IaC / Bicep | `skills/bicep/bicep.skill.md` |

When a domain skill exists for the changed code, that skill's rules **are** the review checklist. Pull the relevant ones; do not restate them here.

## Review process

1. Establish scope: what changed and why (PR description, linked issue, commits).
2. Read the diff in full before judging any single line.
3. For each changed area, open the matching source(s) above and check the change against their rules.
4. Ground every finding in an explicit Principle ID (`A.x`), a security/global default, or a named rule from a domain skill. Never raise an ungrounded opinion.
5. Classify each finding by severity. Assign a verdict.

## Severity levels

- **Blocker** — must fix before merge. Principle violation, security defect, data-loss or correctness bug.
- **Major** — should fix before merge. Design smell, missing validation, untested critical path.
- **Minor** — fix soon. Readability, naming, small duplication.
- **Nit** — optional. Style preference, non-blocking.

## Verdict format

```
## Review — <change name>

### Scope
<one line: what changed and why>

### Findings
- [Blocker] <file:line> — <issue>. Ref: <A.x / default / skill rule>. <fix direction>
- [Major]   <file:line> — ...
- [Minor]   <file:line> — ...
- [Nit]     <file:line> — ...

### Verdict
Approve | Approve with nits | Request changes

<one-line rationale tied to the highest-severity finding>
```

## Rules

- Every finding cites its source — a Principle ID, a global/security default, or a named domain-skill rule. No ungrounded opinions.
- Never infer or invent principles (see `principles.instructions.md`); if none applies, frame it as a Minor/Nit quality note.
- A single unresolved **Blocker** means **Request changes** — never approve over a blocker.
- Acknowledge what is done well; review is not only fault-finding.
- Review the change, not the author. Suggest direction; do not rewrite their work.
