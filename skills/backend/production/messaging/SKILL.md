---
name: messaging
description: Guidelines and constraints for designing and implementing messaging-based and event-driven systems. Focuses on reliability, scalability, and consistency.
---

You are working with messaging systems and event-driven architectures. Follow these conventions and constraints to ensure reliable and maintainable integrations.

## Core principles

- Design for **asynchronous communication**
- Systems must be **resilient to failure**
- Ensure **idempotency**
- Embrace **eventual consistency**
- Messages are **contracts**

---

## Message design

- Messages must be clear and stable

### Rules

- Use explicit contracts (DTOs)
- Include only required data
- Avoid breaking changes
- Messages should be self-contained

---

## Events vs Commands

- Distinguish clearly between intent and fact

### Rules

- Events = something that happened
- Commands = something that should happen
- Do not mix semantics

---

## Idempotency

- All message handlers must be idempotent

### Rules

- Processing the same message multiple times must not cause issues
- Use idempotency keys where needed
- Handle duplicate messages gracefully

---

## Error handling and retries

- Handle failures explicitly

### Rules

- Implement retry logic for transient failures
- Avoid infinite retry loops
- Use dead-letter queues for failed messages
- Monitor failed messages

---

## Message processing

- Keep handlers simple and focused

### Rules

- One responsibility per handler
- Do not combine multiple unrelated actions
- Avoid long-running message processing

---

## Ordering

- Do not rely on message ordering unless guaranteed

### Rules

- Design systems to handle out-of-order messages
- Do not assume sequence unless explicitly enforced

---

## Transactions and consistency

- Messaging is eventually consistent by default

### Rules

- Avoid distributed transactions
- Use patterns like:
  - outbox pattern
  - retry compensation
- Keep operations atomic within boundaries

---

## Performance

- Design for high throughput

### Rules

- Process messages asynchronously
- Avoid blocking operations
- Scale consumers horizontally where possible

---

## Message size

- Keep messages small

### Rules

- Do not send large payloads
- Send references instead of full datasets when needed

---

## Observability

- Ensure full traceability

### Rules

- Include correlation IDs in messages
- Log message processing lifecycle
- Track failures and retries

---

## Security

- Validate and protect messages

### Rules

- Do not trust message content blindly
- Validate data before processing
- Do not include secrets in messages

---

## Anti-patterns (avoid)

- Non-idempotent message handlers
- Large, bloated messages
- Tight coupling between producers and consumers
- Ignoring failed messages
- Relying on message ordering
- Long-running or blocking handlers
- Mixing business logic across multiple handlers

---

## Definition of done

Messaging implementation is complete when:

- Messages are well-defined and stable
- Handlers are idempotent
- Retry and failure handling is implemented
- No message loss occurs
- Observability is in place
- No sensitive data is exposed

---

## When in doubt

- Assume messages can be duplicated
- Assume failure will happen
- Keep processing simple and predictable
- Design for resilience first