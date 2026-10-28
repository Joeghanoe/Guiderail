---
type: Rule
title: "IAC.1 Diagnostics are proportionate: the audit trail always, the rest when something uses it"
description: Every resource keeps its audit logs; verbose logs and metric export are added only for a named consumer, sent to the cheapest destination that serves it.
rule_id: IAC.1
principle: [/principles/p-08-observable-by-design.md, /principles/p-01-business-before-technology.md]
tags: [iac, monitoring, cost]
applies_to: ["**/*.bicep", "**/*.tf"]
enforced_by: [review]
severity: major
status: stable
---

# Rule

Observability has a price: Log Analytics charges per GB ingested and per day retained, and the verbose
categories of busy resources (storage reads, gateway requests, firewall flows) can cost more than the resource.
So diagnostics follow what they are used for:

| What | When | Where |
|---|---|---|
| Audit logs (the `audit` category group: who changed or read what) | Always, on every resource that has them | The environment's Log Analytics workspace, or an archive storage account when only retention is needed |
| Verbose logs (`allLogs`, request and read logs) | Only when a named consumer needs them: an alert rule, a workbook, an incident runbook | Log Analytics; a low-cost table plan (Basic, Auxiliary) for high volume that is only searched during incidents |
| Metrics | Platform metrics are available without a diagnostic setting; export them (`AllMetrics`) only for alerts or retention beyond the platform's | Log Analytics only when a query needs them |

- Every verbose category in a diagnostic setting names its consumer in a comment. No consumer, no category.
- Retention is a per-environment configurable (IAC.7): short in dev, what the policy requires in production.
- A PR that adds a high-volume category states the expected daily volume or cost.
- A resource without any diagnostic setting is still a finding: the audit trail is not optional.

# Boundary

A compliance or customer requirement that demands full logging wins; it is then a boundary case with the
requirement, an owner and `stale_after`, and the cost is part of the decision.
