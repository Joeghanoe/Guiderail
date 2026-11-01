---
type: Rule
title: "OBS.2 An alert follows causality: it fires when something breaks, and when the proof that it works is missing"
description: An alert is true when the thing works and silent only then; no data, a stopped signal or a check that cannot run counts as broken, not as healthy.
rule_id: OBS.2
principle: /principles/p-08-observable-by-design.md
tags: [observability, alerts, monitoring]
applies_to: ["**/*.bicep", "**/*.tf", "**/*.kql", "**/*.yml", "**/*.cs"]
enforced_by: [review]
severity: major
status: draft
sources:
  - id: origin
    resource: feedback/c-draft-alert-on-absence-of-signal.md
---

# Rule

An alert states a cause and an effect: _if the service works, this signal is present and good; if it breaks, this signal changes or disappears_. Both directions are covered:

- **Works and breaks:** the signal is present and turns bad. The alert fires on the bad value.
- **Does not work and does not break:** the signal is absent or the check cannot run (no rows, a stopped agent, an expired credential, an empty time series). The alert fires on the absence. Silence is never taken as healthy.

In practice:

- Every alert has a _positive_ signal that proves the thing works (a request count, a heartbeat, a successful probe), not only a negative one (an error count). No positive signal means no proof.
- Empty intervals are filled with zero, or the platform's "no data" option is set to alert. A query that returns no rows is a result, not a pass.
- The alert is tested with both inputs: a bad value and no data at all.
- The person reading the alert can tell from it which of the two happened.

# Boundary

A signal that is legitimately absent (a nightly job outside its window, a service scaled to zero on purpose) gets a schedule or condition that says so, written next to the alert. It is not left to silence.
