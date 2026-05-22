---
name: NoSQL / Cosmos DB Development
description: Guidelines and constraints for designing and using NoSQL databases (with focus on Azure Cosmos DB). Ensures scalable, performant, and correct data modeling and usage from backend code.
---

You are working with NoSQL databases, specifically Azure Cosmos DB. Follow these conventions and constraints to ensure scalable, performant, and maintainable solutions.

## Core principles

- Design for **scalability and distribution**
- Model data based on **access patterns**, not normalization
- Prefer **denormalization over joins**
- Optimize for **read and write efficiency**
- Treat the database as a **highly distributed system**

---

## Data modeling

- Model data around how it is accessed
- Store related data together in the same document where possible

### Rules

- Avoid relational thinking (no joins across containers)
- Denormalize where needed
- Keep documents self-contained
- Design for query efficiency, not storage efficiency

---

## Containers and partitioning

- Choose a good partition key upfront

### Rules

- Partition key must:
  - Have high cardinality
  - Distribute load evenly
  - Be present in most queries
- Avoid:
  - Hot partitions
  - Cross-partition queries where possible

---

## Document design

- Keep documents reasonably sized

### Guidelines

- Prefer fewer, richer documents over many small ones
- Avoid deeply nested or overly complex structures
- Keep schema flexible but controlled

---

## Queries

- Optimize queries for performance and RU consumption

### Rules

- Always query using the partition key when possible
- Avoid full container scans
- Only select required fields
- Keep queries simple and predictable

---

## Indexing

- Use indexing effectively

### Rules

- Do not rely on default indexing blindly
- Exclude unused fields to reduce RU cost
- Tune indexing based on query patterns

---

## Consistency

- Choose appropriate consistency level

### Options

- Strong
- Bounded staleness
- Session (default)
- Eventual

### Rules

- Use session consistency for most applications
- Only increase consistency when required

---

## Throughput and RU management

- Design with Request Units (RU) in mind

### Rules

- Optimize queries to reduce RU consumption
- Avoid expensive operations (cross-partition, large scans)
- Monitor RU usage and adjust throughput

---

## Transactions

- Use transactional batches within a partition

### Rules

- Transactions only work within the same partition key
- Design data model accordingly

---

## Using Cosmos DB from C# code

## Core principles

- Keep data access efficient and predictable
- Minimize RU consumption
- Avoid hidden expensive operations

---

## SDK usage

- Use the official Cosmos DB SDK
- Reuse `CosmosClient` (singleton)

### Rules

- Do not create new clients per request
- Configure proper retry policies

---

## Query execution

- Use parameterized queries

### Rules

- Never build queries via string concatenation
- Always filter by partition key if possible
- Use paginated queries (`FeedIterator`)

---

## Performance in code

- Minimize roundtrips to the database

### Rules

- Avoid calling Cosmos inside loops
- Batch operations where possible
- Prefer point reads (`ReadItemAsync`) over queries when retrieving by id

---

## Serialization

- Use clear and consistent models

### Rules

- Control JSON structure explicitly
- Avoid unnecessary properties
- Keep payloads small

---

## Error handling

- Handle Cosmos-specific exceptions

### Rules

- Handle:
  - 404 (not found)
  - 409 (conflict)
  - 429 (throttling)
- Implement retry logic for transient failures (especially 429)

---

## Id handling

- Use meaningful and unique IDs

### Rules

- IDs must be unique within partition
- Avoid random GUIDs if they hurt query patterns
- Consider composite or domain-based IDs

---

## Security

- Never store secrets in documents
- Protect sensitive data

### Rules

- Do not expose sensitive fields via APIs
- Encrypt sensitive data where necessary

---

## Anti-patterns (avoid)

- Treating Cosmos DB like a relational database
- Cross-container joins
- Poor partition key choices
- Large cross-partition queries
- Storing everything in a single container without design
- Excessive document size
- Querying when a point read is possible
- Creating CosmosClient per request
- Ignoring RU costs

---

## Definition of done

Cosmos/NoSQL work is complete when:

- Data model matches access patterns
- Partition key is well chosen
- Queries are efficient and RU-optimized
- No unnecessary cross-partition queries
- Code uses efficient SDK patterns
- Error handling includes retry logic
- No sensitive data is exposed or stored incorrectly

---

## When in doubt

- Think in access patterns, not tables
- Prefer duplication over joins
- Measure RU cost before optimizing blindly
- Follow existing patterns in the codebase
- Ask user