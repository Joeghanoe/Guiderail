---
type: Rule
title: "OBS.3 Operational output is a contract: named events, stable codes, identifiers instead of content"
description: What a run reports is a fixed set of events and fields with stable names and error codes, carries run and source identifiers and counts, and never payloads, names of customer data or credentials.
rule_id: OBS.3
principle: /principles/p-08-observable-by-design.md
tags: [observability, logging, privacy, dotnet]
applies_to: ["**/*.cs"]
enforced_by: [review]
severity: major
status: draft
sources:
  - id: origin
    resource: first greenfield evaluation run (2026-10-29): reports existed but no event catalogue, no error-code catalogue and no status or health call
---

# Rule

- The design lists the events a run emits (started, per source started and finished, finished) and their
  properties. Event and property names are constants (CODE.4): an alert or a report depends on them, and a
  rename must break a test.
- Events are emitted through one event sink interface (CODE.8). Operations never format or write them; the
  sink does. A test asserts the exact sequence of events on a recording sink, for a success and for a partial failure.
- Every event carries the run identifier and, per source, the source identifier, an outcome, counts, bytes,
  a duration and a reason code. Nothing carries file names, payload, exception text or credentials (SEC.2).
- Reason codes come from one catalogue (a type plus a runbook table). An unknown failure maps to a generic code,
  never to the exception message.
- A run can be queried without starting anything: a status call returns the outcome of a run, a health call
  answers OBS.1. An incomplete run is never reported as healthy, and the report names the affected sources.
- A test feeds a sentinel string through input, fault text and payload, and asserts it appears in no event,
  log line, report or alert.

# Boundary

A source may carry a more specific code than the catalogue's generic one, but only by adding it to the
catalogue and the runbook. Tenant or customer identifiers are allowed; resource names only when the customer
agreed and a setting says so.
