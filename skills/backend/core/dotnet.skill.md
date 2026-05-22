---
name: .NET C# Development
description: Guidelines and constraints for writing high-quality C# backend code. Focuses on maintainability, readability, and robustness.
---

You are working on C# backend code. Follow these conventions and constraints to ensure high-quality, maintainable, and robust implementations.


## .NET versioning

- Use the latest .NET LTS version (N) for all new development
- Previous LTS version (N-1) is temporarily allowed for existing systems
- Do not use versions older than N-1
- Do not run end-of-life .NET versions
- Avoid using non-LTS versions (STS) in production unless explicitly required


## Core principles

- Write **clean, readable, and maintainable C# code**
- Follow **SOLID principles**
- Prefer **composition over inheritance**
- Avoid unnecessary abstractions
- Make code **explicit and predictable** (no hidden side-effects)

---

## Naming conventions

- PascalCase → Classes, Interfaces, Enums, Methods
- camelCase → variables, parameters, private fields
- Interfaces should start with `I`

---

## Class design

- Keep classes **small and focused (Single Responsibility)**
- One reason to change per class
- Avoid "God classes"

### Rules

- Max ~200–300 lines per class (guideline, not hard limit)
- Split logic into smaller services when needed
- Prefer clear method names over comments

---

## Methods

- Keep methods short and focused
- One responsibility per method

### Guidelines

- Max ~20–30 lines per method
- Use early returns to reduce nesting
- Avoid deeply nested logic

---

## Dependency Injection

- Use constructor injection
- Depend on abstractions (interfaces), not implementations

### Rules

- No service locator pattern
- No `new` inside business logic for dependencies

---

## Database query usage (C#)

- Do not hardcode complex SQL queries across the codebase
- Keep query logic centralized in the data access layer (repositories or query services)

### Rules

- Avoid scattering SQL strings across multiple classes
- Keep queries close to the data access responsibility
- Reuse queries where possible
- Keep queries readable and maintainable

---

## Using Dapper or raw SQL

- Using Dapper or raw SQL is allowed and often preferred for performance-critical scenarios

### Rules

- Always use parameterized queries
- Never build SQL using string concatenation
- Keep SQL predictable and explicit
- Avoid dynamic SQL unless absolutely required

---

## Anti-patterns (avoid)

- SQL queries inside business logic
- Duplicated SQL queries across services
- Large inline SQL blocks in multiple locations
- Building SQL strings with user input
- Mixing SQL logic with domain/business rules

---

## Error handling

- Use exceptions for exceptional cases only
- Do not use exceptions for control flow

### Guidelines

- Throw specific exception types
- Avoid generic `Exception`
- Always include meaningful messages

---

## Null handling

- Avoid null where possible
- Use nullable reference types (`?`) correctly
- Validate inputs explicitly

---

## Collections and LINQ

- Use LINQ for clarity, not complexity
- Avoid multiple enumerations of the same collection

---

## Immutability

- Prefer immutable objects where possible
- Use `record` for value objects

---

## Asynchronous programming

- Use `async/await` consistently
- Only use async for I/O-bound operations

### Rules

- Avoid `.Result` and `.Wait()`
- Always return `Task` or `Task<T>`

---

## Logging

- Log meaningful events, not everything
- Avoid logging sensitive data

---

## Validation

- Validate inputs at boundaries
- Fail fast on invalid data

---

## Interfaces and abstractions

- Use interfaces when:
  - There are multiple implementations
  - You need testability

### Avoid

- Interfaces "just in case"
- One-to-one interface-implementation without reason

---

# Secrets and sensitive data

- Never store secrets in source code
- Never hardcode:
  - API keys
  - Connection strings with credentials
  - Tokens or passwords
- Load secrets from secure configuration sources (environment variables, secret stores)

### Rules

- Treat all secrets as external configuration
- Do not expose secrets via logs, exceptions, or API responses
- Avoid committing sensitive values in:
  - appsettings.json
  - launchSettings.json
  - test data
- Use placeholders in configuration files instead of real values

---

## Testing mindset

- Write testable code (even if tests are written elsewhere)
- Avoid static dependencies
- Keep side effects isolated

---


## Anti-patterns (avoid)

- God classes
- Static service classes
- Deeply nested conditionals
- Over-engineering / premature abstraction
- Magic strings (use constants)
- Hidden side effects
- Large constructors with many dependencies

---

## Definition of done

Code is complete when:

- It is clean and readable
- Responsibilities are well separated
- No unnecessary complexity
- Proper error handling is implemented
- No hidden side effects
- Naming is clear and consistent

---

## When in doubt

- Prefer readability over cleverness
- Keep it simple
- Follow existing patterns in the codebase
- Ask user