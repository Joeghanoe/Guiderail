---
name: mssql
description: Guidelines and constraints for designing, querying, and integrating with Microsoft SQL Server databases. Focuses on performance, maintainability, and correct usage from backend code.
---

You are working with Microsoft SQL Server. Follow these conventions and constraints to ensure reliable, performant, and maintainable database interactions.

## Core principles

- Design for **data integrity and consistency**
- Optimize for **performance and scalability**
- Keep database logic **clear and maintainable**
- Minimize coupling between database and application code
- Treat the database as a **critical shared resource**

---

## Database design

- Use normalized schemas unless denormalization is required for performance
- Use appropriate data types

### Rules

- Avoid using `nvarchar(max)` unless necessary
- Use `datetime2` instead of `datetime`
- Use `bit` for boolean values
- Define explicit constraints (PK, FK, UNIQUE)

---

## Naming conventions

- Use PascalCase for tables and columns
- Use singular table names

### Examples (guideline, no code implementation required)

- `Order`
- `OrderItem`
- `CreatedAt`

### Rules

- Avoid abbreviations unless widely understood
- Keep names descriptive and consistent

---

## Keys and indexing

- Every table must have a primary key
- Use clustered indexes wisely

### Rules

- Avoid GUID fragmentation (use sequential GUIDs when needed)
- Create indexes on frequently queried columns
- Do not over-index (impacts write performance)
- Regularly review index usage

---

## Queries

- Write efficient, predictable queries

### Rules

- Avoid `SELECT *`
- Only select required columns
- Use proper filtering
- Avoid unnecessary joins
- Ensure queries are covered by indexes where possible

---

## Transactions

- Use transactions only when needed

### Rules

- Keep transactions short
- Avoid long-running locks
- Ensure proper rollback on failure

---

## Stored procedures vs inline queries

- Prefer simple, readable queries from code
- Use stored procedures when:
  - Performance is critical
  - Complex logic is required
  - Reuse is needed across multiple services

---

## Data integrity

- Enforce rules at database level

### Rules

- Use foreign keys
- Use constraints for validation
- Do not rely solely on application validation

---

## Pagination

- Always paginate large datasets

### Rules

- Use `OFFSET / FETCH`
- Avoid returning unbounded result sets

---

## Security

- Use least-privilege access
- Never expose database directly to clients

### Rules

- Do not store secrets in the database
- Protect sensitive data
- Avoid dynamic SQL where possible (risk of injection)

---

## Performance

- Monitor and optimize slow queries
- Use execution plans for analysis

### Guidelines

- Avoid N+1 query patterns
- Reduce roundtrips between app and database
- Batch operations when possible

---

## Using MSSQL from C# code

### Core principles

- Keep business logic **out of SQL where possible**
- Keep data access **efficient and predictable**
- Avoid unnecessary abstraction layers

---

## Data access patterns

- Use repositories or data access services
- Keep queries close to the use case

### Rules

- Do not mix query logic with business logic
- Keep data layer focused on data retrieval and persistence

---

## Parameterization

- Always use parameterized queries

### Rules

- Never concatenate SQL strings with user input
- Prevent SQL injection by design

---

## ORM usage (e.g. Entity Framework)

- Use ORM for standard CRUD operations
- Be explicit when performance matters

### Rules

- Avoid heavy, complex LINQ queries that are hard to translate
- Inspect generated SQL when needed
- Disable lazy loading unless explicitly required
- Use `AsNoTracking` for read-only queries
- Prevent N+1 queries with proper includes

---

## Performance in code

- Minimize database roundtrips

### Rules

- Batch queries where possible
- Avoid calling the database inside loops
- Cache results when appropriate

---

## Transactions in code

- Use transactions only when required

### Rules

- Keep transaction scope small
- Ensure rollback on failure
- Avoid distributed transactions unless absolutely necessary

---

## Mapping

- Map database models to domain or DTO models

### Rules

- Do not expose database entities directly
- Keep mapping explicit and controlled

---

## Error handling

- Handle database exceptions properly

### Rules

- Do not expose raw SQL errors to clients
- Log detailed errors internally
- Translate database errors to meaningful application errors

---

## Anti-patterns (avoid)

- `SELECT *` in production queries
- Dynamic SQL with string concatenation
- Business logic in stored procedures (unless justified)
- Database calls inside loops
- Returning large unfiltered datasets
- Tight coupling between DB schema and API models
- Overuse of ORM without understanding generated queries

---

## Definition of done

Database work is complete when:

- Schema is consistent and well-defined
- Queries are performant and optimized
- Indexing is appropriate
- Data integrity is enforced
- Code uses safe and efficient data access patterns
- No SQL injection risks exist

---

## When in doubt

- Prefer simplicity over complexity
- Measure performance before optimizing
- Follow existing patterns in the codebase
- Validate generated SQL when using ORMs
- Ask user