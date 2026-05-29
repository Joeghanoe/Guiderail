---
name: Backend Observability
description: Guidelines and constraints for logging, monitoring, and tracing backend systems. Ensures systems are observable, debuggable, and production-ready.
---

You are responsible for observability of backend systems. Follow these conventions and constraints to ensure systems are monitorable, traceable, and diagnosable in production.

## Core principles

- Systems must be **observable by design**
- Logging, metrics, and tracing are **first-class concerns**
- Every request must be **traceable end-to-end**
- Failures must be **detectable and diagnosable**
- Prefer **structured data over text logs**

---

## Logging

- Use structured logging

### Rules

- Include contextual data (e.g. identifiers, state)
- Use consistent log formats
- Log meaningful events only
- Use appropriate log levels:
  - Information → normal flow
  - Warning → unexpected but handled
  - Error → failures

---

## Correlation and tracing

- Every request must have a correlation ID

### Rules

- Generate or propagate correlation IDs
- Pass correlation IDs across:
  - API calls
  - messaging systems
  - background jobs
- Include correlation ID in all logs

---

## Distributed tracing

- Systems must support tracing across components

### Rules

- Track full request flow across services
- Ensure trace continuity in async flows
- Link logs, dependencies, and operations

---

## Metrics

- Capture key performance indicators

### Rules

- Track:
  - request duration
  - failure rates
  - throughput
- Use metrics for alerting and dashboards
- Prefer aggregated metrics over logs for monitoring

---

## Error observability

- All errors must be visible and traceable

### Rules

- Log all unhandled exceptions
- Include:
  - error type
  - message
  - context (without sensitive data)
- Ensure errors can be linked to requests via correlation ID

---

## Dependency tracking

- Track external dependencies

### Rules

- Log calls to:
  - databases
  - APIs
  - messaging systems
- Include:
  - duration
  - success/failure
- Identify slow or failing dependencies

---

## Health monitoring

- Expose system health

### Rules

- Implement health checks
- Validate:
  - database connectivity
  - external dependencies
- Differentiate:
  - liveness (is it running)
  - readiness (can it handle traffic)

---

## Logging boundaries

- Log at system boundaries

### Rules

- Log:
  - incoming requests
  - outgoing calls
  - message processing start/end
- Avoid excessive logging inside tight loops

---

## Sensitive data

- Never log sensitive data

### Rules

- Do not log:
  - secrets
  - tokens
  - personal data (unless masked)
- Sanitize data before logging

---

## Performance considerations

- Logging should not degrade performance

### Rules

- Avoid excessive logging in high-throughput paths
- Use asynchronous logging where possible
- Avoid large log payloads

---

## Consistency

- Logs and metrics must be consistent across services

### Rules

- Use consistent naming for:
  - events
  - properties
  - identifiers
- Align logging structure across the system

---

## Anti-patterns (avoid)

- Logging everything (noise)
- Logging nothing (no visibility)
- Unstructured logs
- Missing correlation IDs
- Logging sensitive data
- Silent failures
- No monitoring on critical paths

---

## Definition of done

Observability is complete when:

- All requests are traceable end-to-end
- Logs are structured and meaningful
- Metrics are available for key flows
- Errors are visible and diagnosable
- Dependencies are monitored
- No sensitive data is logged

---

## When in doubt

- Add context
- Make behavior observable
- Prefer structured logs over text
- Ensure traceability across boundaries
