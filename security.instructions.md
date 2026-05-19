---
applyTo: "**"
---

# Security Principles

Apply to all code changes. These are language-agnostic security principles.

## S.1: Least Privileged
A subject should be given only those privileges needed to complete its task. Reduces risk of attackers gaining access via compromised low-privilege accounts.
- [Critical] Over-permissive CORS: `AllowAnyOrigin()` + `AllowAnyMethod()`, wildcard permissions
- [Critical] Wildcard roles/policies: `*` permissions, admin roles assigned for regular operations
- [Major] Excessive scopes: tokens or service principals granted more permissions than required

## S.2: Just in Time
Provide privileges on demand for the minimum time required, then revoke. Every access control action must be auditable.
- [Critical] Permanent elevated access: long-lived admin tokens or credentials without expiry
- [Major] Missing access reviews: standing privileged roles without time-bound grants
- [Major] Non-auditable access: privilege grants or revocations not logged

## S.3: Minimize Attack Surface Area
Restrict the functions users can access to reduce potential vulnerabilities. Every added feature increases risk.
- [Critical] Debug/admin endpoints in production: `/debug`, `/admin`, `/swagger` exposed without auth
- [Major] Unused dependencies: packages or features included but not needed
- [Major] Unnecessary exposed ports or services: services listening beyond what is required

## S.4: Establish Secure Defaults
The application must be secure by default. Users should take deliberate steps to reduce security, not increase it.
- [Critical] Disabled security: `[AllowAnonymous]` on data endpoints, `RequireHttpsMetadata = false`, `ValidateIssuer = false`
- [Critical] Debug settings in prod: development/debug configuration in production code paths
- [Major] Weak default passwords or open registrations: no complexity rules, no verification on sign-up

## S.5: Defense in Depth
Multiple security controls that approach risks in different ways. Never rely on a single layer of protection.
- [Major] Single validation layer: client-only validation, auth without server-side authorization checks
- [Major] Missing server-side validation: data validated only on client but not on server
- [Major] No MFA for sensitive operations: authentication relying solely on username and password

## S.6: Fail Securely
Applications must fail without granting additional privileges or exposing sensitive information.
- [Critical] Exposed exceptions: `ex.ToString()`, `ex.StackTrace`, `ex.Message` in API responses
- [Critical] Verbose errors to clients: internal paths, connection strings, or system info in error responses
- [Major] Failing open: errors that default to granting access rather than denying it

## S.7: Segregation of Duties
Prevent individuals from acting fraudulently by separating responsibilities. Users should not hold conflicting roles.
- [Critical] Conflicting roles: same identity can both initiate and approve sensitive operations
- [Major] Missing approval workflows: destructive or financial actions without a second approver
- [Major] Admin accounts used for end-user operations: service accounts with elevated rights used for routine tasks

## S.8: Avoid Security by Obscurity
Security must never rely on hiding functionality, URLs, or source code. Sufficient controls must exist independently.
- [Critical] Hidden endpoints: unprotected "secret" URLs where obscurity is the only protection
- [Critical] Security through complexity: obfuscated logic used as a substitute for proper access controls
- [Major] Undocumented security assumptions: controls that only work if an attacker lacks specific knowledge

## S.9: Fix Security Issues Correctly
Identify root causes of security issues, repair them thoroughly, and test fixes. Check all systems using the same pattern.
- [Critical] SQL injection: string concatenation in SQL queries instead of parameterized queries
- [Critical] Path traversal: unsanitized user input used in file paths
- [Critical] Hardcoded secrets: connection strings, passwords, API keys, or tokens in code
- [Critical] PII exposure: sensitive data in logs, outputs, or error messages
- [Major] Partial fixes: patching one occurrence without checking other systems using the same pattern

## S.10: Keep Security Simple
Avoid overly sophisticated security architectures. Complexity increases the risk of errors and misconfigurations.
- [Major] Reinventing security primitives: custom crypto, custom token schemes, or hand-rolled auth instead of proven libraries
- [Major] Unnecessary security complexity: layered indirection that obscures whether controls are actually enforced
- [Minor] Inconsistent security patterns: different auth/validation approaches across similar endpoints in the same service
