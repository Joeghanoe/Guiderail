---
type: Principle
title: "P8 Observable by Design"
description: Monitoring, logging, tracing, metrics and health make a system governable.
principle_id: P8
tags: [observability]
status: stable
sources:
  - id: vegviser
    resource: TeamValue.Vegviser@2feca0e:00-foundation/Principles.md#L129-L144
---

# P8 Observable by Design

Monitoring, logging, tracing, metrics and health make a system governable.

Vegviser is the authority for this principle; the applications below record approved harness guidance.[^vegviser] Read the source when a finding depends on the exact wording. A deviation follows Vegviser's Exception and Risk Acceptance playbook.

[^vegviser]: Vegviser Principles, P8

# Application to dependencies

Health describes the ability to deliver the service's capabilities, including the external systems those capabilities require. Monitoring makes complete failure, partial failure and uncertain health visible at the scope affected. Ownership determines who responds; it does not determine whether a dependency is observed. A tenant-specific outage must remain visible without declaring unaffected tenants unavailable.

Concrete health responses and alert behavior live in OBS.1 and OBS.2. The harness requires observable capability impact without prescribing a health endpoint name, monitoring product or probe location.

# Application to trace correlation

Use W3C trace context for distributed execution tracing. Where a business workflow spans retries or multiple traces, also carry a stable business or event correlation identifier. Document and verify how both propagate across synchronous and asynchronous boundaries. An arbitrary correlation identifier does not substitute for valid trace context; do not force distinct executions into one trace merely because they belong to the same business workflow.

Supporting context: Loop page "Data Principles" (D.2); user decisions and health clarification 2026-10-29.
