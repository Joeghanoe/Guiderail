---
name: api
description: Guidelines and constraints for designing and implementing robust, secure, and maintainable backend APIs.
---

You are working on backend APIs. Follow these conventions and constraints to ensure consistency, reliability, and clarity for all API consumers.

## Core principles

- Build **predictable and consistent APIs**
- Design for **clarity and usability**
- Ensure **backward compatibility**
- Keep APIs **stateless**
- Prioritize **security and validation**

---

## API design

- Follow RESTful conventions
- Use resource-based naming (nouns, not verbs)
- Keep endpoints intuitive and discoverable

### Rules

- Use plural resource names
- Avoid deeply nested routes
- Keep URLs clean and predictable

---

## HTTP methods

Use correct HTTP verbs:

- GET → retrieve data
- POST → create resources
- PUT → full update
- PATCH → partial update
- DELETE → remove resource

### Rules

- Do not misuse POST for reads
- Ensure idempotency for PUT and DELETE

---

## Status codes

Return correct HTTP status codes:

- 200 → success
- 201 → created
- 204 → no content
- 400 → bad request
- 401 → unauthorized
- 403 → forbidden
- 404 → not found
- 500 → server error

### Rules

- Do not always return 200
- Be explicit and consistent

---

## Request validation

- Validate all incoming data at API boundaries
- Reject invalid input immediately

### Rules

- Never trust client input
- Return clear validation errors
- Do not pass invalid data to business logic

---

## Response design

- Use consistent response structures
- Return only necessary data

### Guidelines

- Avoid exposing internal models
- Use DTOs for API contracts
- Keep responses stable over time

---

## Versioning

- Version APIs explicitly

### Options

- URL versioning (`/v1/orders`)
- Header-based versioning

### Rules

- Never break existing clients
- Introduce new versions for breaking changes

---

## Error handling

- Return structured error responses

### Guidelines

- Include:
  - error code
  - message
  - trace/correlation id (if available)
- Do not expose internal implementation details

---

## Authentication and authorization

- Protect all non-public endpoints
- Validate identity and permissions before processing

### Rules

- Never rely on client-side checks
- Enforce authorization at API level
- Deny by default

---

## Pagination, filtering, sorting

- Always paginate large datasets

### Rules

- Use query parameters for filtering and sorting
- Avoid returning large, unbounded collections -> use paginazation instead

---

## Idempotency

- Ensure safe retries for critical operations

### Rules

- Use idempotency keys where needed
- Avoid duplicate processing

---

## Security

- Validate and sanitize inputs
- Protect against:
  - injection attacks
  - over-posting
  - mass assignment

### Rules

- Never expose sensitive data in responses
- Never leak internal IDs if they should be hidden

---

## Logging and observability

- Log all important API actions
- Include correlation identifiers

### Rules

- Do not log sensitive data
- Ensure errors are traceable

---

## Performance

- Keep APIs fast and efficient
- Minimize payload size

### Guidelines

- Use pagination
- Avoid unnecessary computations
- Cache where appropriate

---

## Consistency

- Follow consistent naming and structure across all endpoints
- Reuse patterns

### Rules

- Same input → same structure
- Same errors → same format

---

## Anti-patterns (avoid)

- Fat controllers with business logic
- Inconsistent response formats
- Returning raw database entities
- Ignoring HTTP semantics
- Overloaded endpoints with multiple responsibilities
- Silent failures or unclear errors

---

## Definition of done

An API is complete when:

- It follows REST conventions
- Inputs are validated
- Responses are consistent
- Errors are structured and clear
- Security is enforced
- No sensitive data is exposed
- Behavior is predictable and documented

---

## When in doubt

- Prefer simplicity over flexibility
- Be explicit rather than implicit
- Follow existing API patterns
- Ask user