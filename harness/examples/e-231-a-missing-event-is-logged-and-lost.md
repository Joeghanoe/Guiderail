---
type: Example
title: "E-231 A queue function logs an error and returns, so the message is completed and lost"
description: A function that finds no event data logs at Error and returns normally; throw, or reject the message to the dead-letter queue, so the loss is visible where the platform reports failures.
example_id: E-231
rule: /rules/code/code-2-fail-loudly.md
verdict: violation
status: draft
tags: [errors, queue, observability]
example_file: src/WebhookReceivedFunction.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T09:00:00Z }
sources:
  - id: evidence
    resource: b2b-hook@WebhookReceivedFunction.cs#L35-L56
  - id: evidence-contrast
    resource: b2b-hook@WebhookReceivedFunction.cs#L98-L111
---

# Situation

A function is triggered by a queue message, deserialises it into an event and reads `event.Data`. When `Data` is null it
logs "No event data found" with `LogError` and `return`s. A few lines later, a missing account id throws, and the `catch`
block records a failure event and rethrows.[^evidence]

# Why (verdict)

Both are the same situation, a malformed message, handled in two ways. The `return` completes the message: the platform sees
a successful invocation, the failure-rate alert (which counts failed invocations and a custom failed flag) stays quiet, and
the payload is gone. The later `throw` is the compliant half: the invocation fails, the telemetry carries `Failed = 1`, and the
queue's delivery count decides on retry or dead-letter (CODE.2). Make the null check throw, and put it inside the `try` so
the `finally` records it. The message body also should not go into the log (SEC.2).

# Compliant pattern

## Good example

```csharp
var evt = JsonConvert.DeserializeObject<WebhookEvent>(body)
    ?? throw new InvalidDataException("Message body is not a webhook event.");

var data = evt.Data
    ?? throw new InvalidDataException($"Event {evt.Id} has no data.");
```

## Bad example

```csharp
var incomingEvent = webhookEvent.Data;
if (incomingEvent == null)
{
    _logger.LogError("No event data found in the incoming event");
    return;
}
```

# Not verified

Not run. In the source the retry count on the queue is 1, so a throw dead-letters straight away; that was read in the infrastructure
module of the sibling app, not this one.

[^evidence]: Entry-point function of a webhook-to-case function app.
