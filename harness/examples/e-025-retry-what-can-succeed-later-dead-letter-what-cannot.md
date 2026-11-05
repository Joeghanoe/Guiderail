---
type: Example
title: "E-025 Retry a failure that can succeed later, dead-letter one that never will"
description: A queue handler lets the broker retry transient failures but immediately dead-letters permanent errors with a clear reason code.
example_id: E-025
rule: /rules/code/code-2-fail-loudly.md
verdict: compliant
status: stable
verified: { by: human:teamvaluegroup, at: 2026-11-01T19:28:57Z }
tags: [errors, messaging, retry, dead-letter]
example_file: src/MessageHandler.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T10:00:00Z }
---

# Situation

A message handler encounters both transient issues (timeouts, throttling) and permanent failures (malformed payloads, invalid data, duplicate entries).

# Why (verdict)

Failures should fail loudly according to their type ([CODE.2](../rules/code/code-2-fail-loudly.md)):

- Rethrow transient failures so the message broker handles retries and delivery limits.
- Immediately dead-letter permanent failures with a fixed error code to prevent wasteful retries and queue delays ([SEC.2](../rules/security/sec-2-no-secrets-or-personal-data.md), [OBS.3](../rules/observability/obs-3-operational-output-is-a-contract.md)).

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
    throw;                                                    // redelivered; logged where it is finally handled (CODE.2)
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
