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

## Standardization

- **A.1** — Prefer SaaS over PaaS. Justify any deviation.
- **A.3** — One framework per frontend domain, one per backend domain.
- **A.20** — Every architectural choice includes a cost estimate.

## Cloud Principles

- **Everything as Code** — No manual portal or infrastructure changes.
- **Four Eyes** — No unreviewed changes reach production.
- **Roll Forward** — Fix forward, no rollbacks.
- **DRY** — No duplicated logic or configuration.
- **Interfaces are Versioned** — Always version before publishing.
- **Everything is Auditable** — Full traceability required on all operations.
- **POLA** — Principle of Least Astonishment. Behavior must be predictable.
- **All code is testable** — No feature ships without a test.
- **Clean Code** — Readable, maintainable, and consistent codebase.

## Security

- **S.1** — Least privilege on all identities and access.
- **S.3** — Minimize attack surface. No unnecessary exposure.
- **S.5** — Defense in depth.
- **S.6** — Fail securely. No sensitive data in error responses or logs.
- **S.7** — Segregation of duties.
