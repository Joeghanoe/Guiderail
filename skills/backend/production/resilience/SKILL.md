---
name: resilience
description: Guidelines and constraints for building resilient backend systems. Focuses on handling failures, retries, and ensuring system stability under load and partial outages.
---

You are responsible for building resilient backend systems. Follow these conventions and constraints to ensure systems handle failures gracefully and remain stable under real-world conditions.

## Core principles

- Failure is **inevitable**
- Systems must be **resilient by design**
- Design for **partial failure**, not full success
- Prefer **graceful degradation over hard failure**
- Protect systems from cascading failures

---

## Failure handling

- Always assume dependencies can fail

### Rules

- Handle failures explicitly
- Distinguish between:
  - transient failures (retryable)
  - permanent failures (non-retryable)
- Do not ignore or swallow exceptions

---

## Retry strategy

- Implement retries for transient failures only

### Rules

- Use exponential backoff
- Limit retry attempts
- Avoid aggressive retry loops
- Add jitter to prevent retry storms
- Do not retry non-idempotent operations blindly

---

## Idempotency

- All retryable operations must be idempotent

### Rules

- Repeated execution must not cause unintended side effects
- Use idempotency keys where needed
- Ensure safe retries for:
  - API calls
  - message handling
  - background jobs

---

## Timeouts

- Always define timeouts for external calls

### Rules

- Do not allow infinite waiting
- Fail fast when dependencies are slow
- Choose realistic timeout values per dependency

---

## Circuit breaker pattern

- Prevent repeated calls to failing dependencies

### Rules

- Open circuit when failure threshold is reached
- Allow recovery after cooldown period
- Avoid overwhelming failing systems

---

## Bulkhead pattern

- Isolate system components

### Rules

- Separate critical and non-critical workloads
- Prevent one failure from affecting the entire system
- Limit resource usage per component

---

## Fallback strategies

- Provide fallback behavior when possible

### Rules

- Return cached data if available
- Degrade functionality gracefully
- Avoid complete system failure

---

## Messaging resilience

- Messaging systems must handle failure scenarios

### Rules

- Use retries with backoff
- Use dead-letter queues for failed messages
- Ensure idempotent message handlers
- Monitor message failures and reprocessing

---

## API resilience

- APIs must handle downstream failures gracefully

### Rules

- Do not expose raw dependency failures
- Return appropriate error responses
- Implement retries only when safe
- Avoid blocking threads on slow dependencies

---

## Resource protection

- Protect system resources under load

### Rules

- Limit concurrency when needed
- Prevent resource exhaustion
- Use backpressure strategies where applicable

---

## Observability integration

- Resilience must be observable

### Rules

- Log retries and failures
- Track retry counts and failure rates
- Monitor circuit breaker states
- Surface degraded system states

---

## Anti-patterns (avoid)

- Infinite retry loops
- Retrying non-idempotent operations
- Ignoring transient vs permanent errors
- No timeout on external calls
- Tight coupling to unreliable dependencies
- Cascading failures across services
- Silent failures without logging

---

## Definition of done

A resilient system is complete when:

- Failures are handled explicitly
- Retry strategies are implemented correctly
- Operations are idempotent where needed
- Timeouts are configured
- Dependencies are protected with circuit breakers
- No cascading failures occur under stress
- Failures are observable and traceable

---

## When in doubt

- Assume dependencies will fail
- Fail fast and recover gracefully
- Limit retries and protect systems
- Prefer resilience over perfect success
- Ask User