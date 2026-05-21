---
description: Global TeamValue engineering defaults — applies in every conversation.
---

# TeamValue Global Instructions

## Defaults

- Use `DefaultAzureCredential` — never connection strings or embedded secrets.
- Every Azure resource requires diagnostic settings (`audit` + `allLogs` + `AllMetrics` → Log Analytics).
- `disableLocalAuth: true` on all resources that support it.
- Managed Identity (`SystemAssigned`) + RBAC — no service principal secrets, no access policies.
- Key Vault: `enableRbacAuthorization: true`, `enablePurgeProtection: true`, `enableSoftDelete: true`.
- Network ACLs: `defaultAction: Deny`, `bypass: AzureServices` on every resource.
- TLS 1.2+; disable CBC, TripleDES, TLS 1.0/1.1, SSL 3.0.
- No PII in logs, ever.
- Roll Forward — never rollback; release a forward fix as a new deployment.
- Framework version: n-1 (current stable minus one).

## Comment style

Explain WHY, not WHAT. No decorative separator lines. No echo comments.

## TeamValue principles

Full principles: `C:\Users\Verst\source\repos\werk\files\TeamValue Principles & Context\`
