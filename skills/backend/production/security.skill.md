---
name: Backend Security
description: Guidelines and constraints for securing backend services, APIs, and data. Focuses on authentication, authorization, and protection against common vulnerabilities.
---

You are responsible for backend security. Follow these conventions and constraints to ensure systems are secure by design.

## Core principles

- Security is **not optional**
- Always follow **least privilege**
- Never trust client input
- Fail securely (deny by default)
- Security must be enforced on the **server side**

---

## Authentication

- Always authenticate users before granting access

### Rules

- Use industry-standard protocols (e.g. OAuth, OpenID Connect)
- Do not build custom authentication mechanisms
- Validate tokens on every request
- Reject expired or invalid tokens immediately

---

## Authorization

- Always verify permissions after authentication

### Rules

- Enforce authorization in backend, not frontend
- Use role-based or policy-based authorization
- Deny access by default
- Do not rely on client-provided roles or claims without validation

---

## Input validation

- Validate all incoming data

### Rules

- Never trust user input
- Validate at API boundaries
- Reject invalid or unexpected fields
- Use strict models (no over-posting)

---

## Data protection

- Protect sensitive data at all times

### Rules

- Never expose sensitive data in API responses
- Mask or omit sensitive fields
- Encrypt sensitive data where required
- Avoid storing unnecessary personal data (data minimization)

---

## Secrets management

- Never store secrets in source code

### Rules

- Do not hardcode:
  - API keys
  - connection strings with credentials
  - tokens or passwords
- Use secure configuration sources (environment variables, secret stores)
- Rotate secrets regularly

---

## Injection prevention

- Protect against injection attacks

### Rules

- Always use parameterized queries
- Never build queries using string concatenation
- Sanitize inputs where applicable
- Avoid dynamic execution of user input

---

## API security

- Secure all endpoints

### Rules

- Require authentication unless explicitly public
- Use HTTPS only
- Validate all request headers and payloads
- Implement rate limiting where needed

---

## Error handling

- Do not leak sensitive information

### Rules

- Do not expose stack traces or internals to clients
- Return generic error messages
- Log detailed errors internally only

---

## Logging

- Log security-relevant events

### Rules

- Log:
  - authentication failures
  - authorization failures
  - suspicious activity
- Never log secrets or sensitive data
- Ensure logs are tamper-resistant

---

## Dependency security

- Keep dependencies secure

### Rules

- Regularly update packages
- Avoid vulnerable or unmaintained libraries
- Monitor for security advisories

---

## Anti-patterns (avoid)

- Trusting client-side validation
- Hardcoded secrets in code
- Exposing internal error details
- Skipping authorization checks
- Custom-built authentication systems
- Logging sensitive data
- Allowing over-posting or mass assignment

---

## Definition of done

Security is correctly implemented when:

- Authentication is enforced
- Authorization is correctly validated
- All inputs are validated
- No sensitive data is exposed
- No secrets are present in code
- APIs are protected against common attacks

---

## When in doubt

- Deny access
- Validate everything
- Assume input is malicious
- Follow existing security patterns