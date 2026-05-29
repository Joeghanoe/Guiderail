---
name: frontend-security
description: Frontend security guardrails and review checklist for TeamValue UI changes.
---

Use this skill during implementation and review to enforce client-side security and quality gates.

## Security guardrails

- **S.3** - Never expose secrets or sensitive data client-side.
- **S.6** - Fail securely. Do not leak sensitive data in UI error states or logs.
- Minimize exposed surface area in routes, data payloads, and client-visible diagnostics.

## Mandatory review checklist

- Are secrets and sensitive fields excluded from client-visible state and payloads (**S.3**)?
- Do error states avoid sensitive data in rendered messages and console output (**S.6**)?
- Are privileged flows gated before data requests (**S.3**)?
- Are loading, error, and redirect outcomes explicit and predictable (POLA)?
- Are generated components untouched and composed instead (**A.19**)?
