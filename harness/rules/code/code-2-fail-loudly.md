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
- Do not log request or response bodies ([SEC.2](../security/sec-2-no-secrets-or-personal-data.md)).

# Boundary

A method whose contract is "try" (`TryParse`, a health probe) may return a result instead of throwing, when the result type says what failed.

# Related guidance

This rule applies [P8 Observable by Design](../../principles/p-08-observable-by-design.md).

Worked examples:

- [E-008 A failure is thrown or checked, not swallowed into a null](../../examples/e-008-do-not-swallow-failures.md) (violation).
- [E-023 One failure is logged, tracked and recorded as a custom event, each with the full exception](../../examples/e-023-one-failure-logged-three-times.md) (violation).
- [E-025 Retry a failure that can succeed later, dead-letter one that never will](../../examples/e-025-retry-what-can-succeed-later-dead-letter-what-cannot.md) (compliant).
- [E-028 Integration configuration is deserialised and validated once, and a bad entry fails by name](../../examples/e-028-validate-configuration-when-it-loads.md) (compliant).
- [E-029 A wrapper returns true or default after a failed call, so the handler reports success](../../examples/e-029-a-method-that-returns-true-whatever-happened.md) (violation).
- [E-033 A failed external API response is thrown, not turned into an empty result that advances the checkpoint](../../examples/e-033-a-failed-vendor-call-must-not-look-like-an-empty-page.md) (violation).
