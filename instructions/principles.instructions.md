---
applyTo: '**'
---
# Architectural Principles

## Purpose

Normative architectural principles used by AI agents for guidance and validation.

## Usage by AI Agents

AI agents MUST:
- always reference Principle IDs explicitly
- never infer additional principles
- never reinterpret principles beyond stated intent
- treat principles as mandatory unless explicitly exempted

---

# A.1 – SaaS first, PaaS second
Category: Standardization
Guidance:
- Prefer SaaS solutions over custom-built platforms
- Prefer managed cloud services over self-hosted infrastructure
- Avoid unnecessary infrastructure ownership

---

# A.2 – Best of Suite before Best of Breed
Category: Costs
Guidance:
- Prefer integrated platform ecosystems
- Minimize vendor fragmentation
- Reduce operational complexity and integration costs

---

# A.3 – One development framework / language per domain
Category: Standardization
Guidance:
- Standardize technology stacks within domains
- Reduce cognitive load and operational fragmentation

---

# A.4 – Proven Cloud Design Patterns
Category: Standardization
Guidance:
- Use established cloud-native architectural patterns
- Avoid experimental or unproven approaches for core systems

---

# A.5 – Multi-tenant by design
Category: Costs
Guidance:
- Design systems for tenant isolation and shared scalability
- Avoid single-tenant assumptions

---

# A.6 – Auto scaling by design
Category: Costs
Guidance:
- Systems should scale automatically based on demand

---

# A.7 – Self service by design
Category: Costs
Guidance:
- Reduce operational dependency on centralized teams

---

# A.8 – Independent services
Category: Service design
Guidance:
- Services must be independently deployable and operable

---

# A.9 – Service interface versioning
Category: Service design

Guidance:
- Service contracts must evolve safely

---

# A.10 – Identity and Access Management
Category: Standardization
Guidance:
- Centralize identity and authorization patterns

---

# A.11 – Monitoring
Category: Operability
Guidance:
- Systems must be observable and operable

---

# A.12 – Single service responsibility
Category: Service design
Guidance:
- Services should own a single business capability

---

# A.13 – Fit-for-purpose datastores
Category: Service design
Guidance:
- Select datastores based on workload characteristics

---

# A.14 – Custom code only for business value
Category: Customization
Guidance:
- Avoid unnecessary bespoke implementations

---

# A.15 – Asynchronous before synchronous communication
Category: Communication
Guidance:
- Prefer event-driven and asynchronous integration patterns

---

# A.16 – No direct service dependencies
Category: Communication
Guidance:
- Avoid tight runtime coupling between services

---

# A.17 – Eventual consistency for replication
Category: Data integrity
Guidance:
- Distributed systems should tolerate eventual consistency

---

# A.18 – No shared datastores
Category: Data integrity
Guidance:
- Services must own their own data

---

# A.19 – Reuse at design time, not runtime
Category: Reusability
Guidance:
- Favor reusable patterns and libraries over runtime coupling

---

# A.20 – Cost justification for all decisions
Category: Costs
Guidance:
- All architectural decisions must consider cost impact
