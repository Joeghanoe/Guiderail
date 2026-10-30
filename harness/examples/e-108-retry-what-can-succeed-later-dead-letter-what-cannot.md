---
type: Example
title: "E-108 Retry a failure that can succeed later, dead-letter one that never will"
description: A queue handler lets the broker retry transient failures, and dead-letters permanent ones at once with a reason code, instead of retrying everything or completing the message.
example_id: E-108
rule: /rules/code/code-2-fail-loudly.md
verdict: compliant
status: draft
tags: [errors, messaging, retry, dead-letter]
example_file: src/MessageHandler.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T10:00:00Z }
sources:
  - id: evidence
    resource: hub-conn@src/connector-03/MessageFunctions.cs#L235-L343
---

# Situation

A queue-triggered handler calls a downstream service. Some failures are temporary (timeout, throttling, a
dependency that is down). Others will fail the same way every time (a malformed message, a rejected value, a
duplicate that already exists).[^evidence]

# Why (verdict)

Each kind needs a different ending, and both are loud (CODE.2):

- A failure that can succeed later is rethrown, so the broker redelivers the message and the delivery count
  bounds the retries. Completing the message instead loses the work silently.
- A failure that cannot succeed is dead-lettered at once with a reason code. Retrying it only delays the
  dead letter, repeats side effects and holds up the queue.
- The reason is a code from a fixed catalogue, not the exception text or the payload (SEC.2, OBS.3).

# Compliant pattern

## Good example

```csharp
try
{
    await processor.HandleAsync(message, ct);
    await messageActions.CompleteAsync(message, ct);
}
catch (Exception ex) when (IsTransient(ex))
{
    logger.LogWarning(ex, "Message {MessageId} failed transiently; the broker will retry", message.MessageId);
    throw;                                                    // redelivered until the max delivery count
}
catch (RejectedMessageException ex)
{
    logger.LogError("Message {MessageId} can never succeed: {Code}", message.MessageId, ex.Code);
    await messageActions.DeadLetterAsync(message, deadLetterReason: ex.Code, cancellationToken: ct);
}
```

## Bad example

```csharp
catch (Exception ex)
{
    logger.LogInformation("Done");               // every failure completes the message: the work is lost
}
```

```csharp
catch (Exception)
{
    throw;                                       // a permanently invalid message is retried to the maximum
}
```

# Not verified

Which exceptions count as transient is a per-service decision (`IsTransient` here is illustrative). The
delivery count and the dead-letter handling are queue settings that belong in the design (DEL.4).

[^evidence]: the failure paths of a queue-triggered handler
