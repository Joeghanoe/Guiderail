---
type: Rule
title: "IAC.6 New resources follow the TeamValue naming convention, or the repo's own"
description: New resource names follow {workload}[-{component}]-{env}-{region}-{type} in kebab-example, unless the repo already has an established convention, which then wins.
rule_id: IAC.6
principle: /principles/p-11-standards-enable-innovation.md
tags: [iac, naming]
applies_to: ["**/*.bicep", "**/*.bicepparam", "**/*.tf", "**/*.yml", "**/*.yaml"]
enforced_by: [review]
severity: major
status: stable
---

# Rule

**First look at what the repo already does.** Read the existing names in the pipeline and the IaC. If they follow one consistent convention, a new resource follows that convention, and the repo's `AGENTS.md` records it under "Naming". If the repo has no convention yet, use TeamValue's:

```text
{workload}[-{component}]-{env}-{region}-{type}
```

| Part | Meaning | Examples |
| --- | --- | --- |
| `workload` | the product or service, one word | `orders`, `payments` |
| `component` | optional: the part of the workload, or the tenant for per-tenant resources | `api`, `worker`, `<tenant>` |
| `env` | the pipeline's environment name, never typed by hand | `${{ environment.name }}` gives `dev`, `prd` |
| `region` | short region code | `we` (West Europe), `ne` (North Europe), `de` (T Cloud eu-de) |
| `type` | Cloud Adoption Framework abbreviation | `rg`, `log`, `appi`, `kv`, `func`, `st`, `vnet`, `snet` |

- Lowercase, kebab-example, the parts in this order.
- Resource types that forbid hyphens or limit length (storage accounts, some Key Vaults) keep the same parts in the same order without hyphens, shortened from the workload side: `ordersapidevwest`. The environment and the type are never dropped.
- Never two conventions in one repo. Moving an existing repo to another convention is a decision record (ADR) first: many resource names cannot be changed once created.
- Vegviser has no resource naming standard yet; until it does, this rule is the reference.

# Boundary

Names imposed from outside (a customer's own naming policy, a platform-generated name) win. The repo's `AGENTS.md` says which and why.

# Related guidance

This rule applies [P11 Standards Enable Innovation](../../principles/p-11-standards-enable-innovation.md).

Worked examples:

- [E-005 Resource names follow one convention, built from the environment name](../../examples/e-005-names-follow-one-convention.md) (violation).
