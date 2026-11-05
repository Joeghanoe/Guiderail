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

Concrete health responses and alert behavior live in [OBS.1](../rules/observability/obs-1-health-reflects-reality.md) and [OBS.2](../rules/observability/obs-2-alerts-follow-causality.md). The harness requires observable capability impact without prescribing a health endpoint name, monitoring product or probe location.

# Application to trace correlation

Use W3C trace context for distributed execution tracing. Where a business workflow spans retries or multiple traces, also carry a stable business or event correlation identifier. Document and verify how both propagate across synchronous and asynchronous boundaries. An arbitrary correlation identifier does not substitute for valid trace context; do not force distinct executions into one trace merely because they belong to the same business workflow.

Supporting context: Loop page "Data Principles" (D.2); user decisions and health clarification 2026-10-29.

# Application to operational output

[OBS.3](../rules/observability/obs-3-operational-output-is-a-contract.md) defines the event, identifier and reason-code contract used to observe a run. The [design gate](../gates/design-check.md) checks its structural prerequisites; [deployment verification](../playbooks/verify-deployment.md) inspects the deployed version, health and telemetry.

# Related guidance

The following rules apply this principle:

- [CODE.10 A derived value has one owner, is never accepted from outside, and says when it becomes consistent](../rules/code/code-10-derived-values-have-one-owner.md).
- [CODE.2 Failures surface; they are not swallowed or hidden](../rules/code/code-2-fail-loudly.md).
- [CODE.9 State the input size a component must handle, and shape its algorithm for that size](../rules/code/code-9-shape-the-algorithm-for-its-size.md).
- [IAC.1 Diagnostics are proportionate: the audit trail always, the rest when something uses it](../rules/iac/iac-1-proportionate-diagnostics.md).
- [SEC.2 No secrets or personal data in code, logs, telemetry or prompts](../rules/security/sec-2-no-secrets-or-personal-data.md).
- [T.3 Every test runs in its layer, and every layer's gate is in the pipeline](../rules/testing/t-3-tests-run-in-their-layer.md).
- [T.5 Behaviour the integration suite can reach comes with a scenario](../rules/testing/t-5-behaviour-has-a-scenario.md).
- [T.6 An adapter is proven once against the real dependency, not only against a stand-in](../rules/testing/t-6-adapter-proven-against-the-real-thing.md).
