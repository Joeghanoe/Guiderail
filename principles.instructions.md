---
applyTo: '**'
---

# Architectural Principles

These rules apply across the entire codebase. Always cite the principle ID when flagging a violation.

## Service Design

- **A.8** — Services operate independently. No tight coupling between services.
- **A.9** — All service interfaces are versioned (`/api/v{N}/`), stable, and backward-compatible.
- **A.12** — Every service has a single responsibility.
- **A.13** — Each service owns its own fit-for-purpose datastore. No shared datastores.
- **A.15** — Async-first. Synchronous calls require explicit justification.
- **A.16** — Services do not call each other directly. Use a broker.
- **A.17** — Replicated data is eventually consistent. No distributed transactions.
- **A.18** — Shared datastores between services are not allowed.
- **A.21** — Controlled autonomy. Automation and AI operate within bounded controls; destructive actions always require a human approval gate.

## Standardization

- **A.1** — Prefer SaaS over PaaS. Justify any deviation.
- **A.3** — One framework per frontend domain, one per backend domain.
- **A.20** — Every architectural choice includes a cost estimate.

## Cloud Principles

- **C.1** — Four Eyes. No unreviewed changes reach production.
- **C.2** — No PII in logs. No privacy-sensitive data (email, tokens, passwords) in logs or responses.
- **C.3** — Automated key rollovers. No hardcoded secrets, connection strings, or API keys in code or config.
- **C.5** — Stateless services. No in-process state between requests; externalize all state.
- **C.6** — Just in Time Access. Minimal-scope, time-limited access; no standing admin access to production.
- **C.8** — Roll Forward. Fix forward, no rollbacks.
- **C.9** — DRY. No duplicated logic or configuration.
- **C.11** — Everything as Code. No manual portal or infrastructure changes.
- **C.12** — Versioned interfaces. Always version before publishing.
- **C.14** — Supported frameworks n-1. Only current and immediate predecessor framework version in use.
- **C.15** — Everything is auditable. Full traceability required on all operations.
- **C.16** — POLA. Principle of Least Astonishment. Behavior must be predictable.
- **C.17** — All code is testable. No feature ships without a test.
- **Clean Code** — Readable, maintainable, and consistent codebase.

## Security

- **S.1** — Least privilege on all identities and access.
- **S.2** — Just in Time. Grant access on demand, revoke after use, log every action.
- **S.3** — Minimize attack surface. No unnecessary exposure.
- **S.4** — Secure defaults. Secure out of the box; no debug config or disabled auth in production.
- **S.5** — Defense in depth.
- **S.6** — Fail securely. No sensitive data in error responses or logs.
- **S.7** — Segregation of duties.
- **S.8** — Avoid security by obscurity. Controls must work even if URLs and code are known.
- **S.9** — Fix security issues correctly. No SQL injection, unsanitized paths, hardcoded secrets, or PII in logs.
