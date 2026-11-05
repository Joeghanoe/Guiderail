---
type: Rule
title: "CODE.2 Failures surface; they are not swallowed or hidden"
description: An exception is handled where something useful can be done, otherwise it propagates; a failed response is checked, not ignored; one failure is logged once.
rule_id: CODE.2
principle: /principles/p-08-observable-by-design.md
tags: [code, errors, observability]
applies_to: ["**/*.cs"]
enforced_by: [review]
severity: major
status: stable
verified: { by: human:teamvaluegroup, at: 2026-10-18T18:52:51Z }
sources:
  - id: origin
    resource: recurring pull request review feedback, 2023-2026, one platform team
---

# Rule

- Do not catch an exception to return `null`, `false` or an empty result when the caller cannot tell that from success. Handle it (retry, fallback, a typed result) or let it propagate.
- Throw the exception type that describes the failure. Do not reuse `InvalidOperationException` as a general error. For an HTTP response, `EnsureSuccessStatusCode()` already throws the right one.
- Log a failure once, with the context, in one statement. A failure that is logged and rethrown is logged at the place that finally handles it.
- In a broker-triggered handler, let transient failures propagate for redelivery. Dead-letter a permanently invalid message immediately with a fixed reason code; retrying it cannot make it valid.
- Do not log request or response bodies (SEC.2).

# Boundary

A method whose contract is "try" (`TryParse`, a health probe) may return a result instead of throwing, when the result type says what failed.
