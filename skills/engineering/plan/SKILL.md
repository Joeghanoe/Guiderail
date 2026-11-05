---
name: plan
description: Plan a substantial change as bounded work packages with dependencies and verification evidence. Use when work spans services or needs coordinated handoffs; keep small local changes in one thread.
---

# Plan bounded work

Start from the approved criteria, architecture decisions and source scope. Preserve criterion identifiers and wording rather than rewriting requirements. Missing acceptance criteria go through [specification](../../../harness/playbooks/write-spec.md); unresolved architectural choices belong to the existing decision authority.

Use [workload planning](../../../harness/playbooks/orchestrate-workload.md) when decomposition is useful. Split by independently verifiable outcomes and conflicts, with explicit file ownership, dependencies, inputs, outputs and checks. Assign model tiers only when authorized delegation is available. A plan is not permission to spawn agents or publish changes.

```bash
tvh orchestrate layers --raw -- --spec "<task-description>" --report <report.md>
tvh orchestrate tier --raw -- --task "<package-description>"
```

Output packages linked to the original criteria and their evidence, plus unresolved decisions and a reason when one thread is sufficient. Hand the approved plan to implementation without restarting discovery. Failed or stale evidence remains visible through subsequent handoffs.
