---
type: Example
title: "E-108 Log the cause before a rollback, run the rollback, and rethrow"
description: After a multi-step create fails, the handler logs the original error first, tries to undo, reports a failed undo separately, and rethrows so the message is retried or dead-lettered.
example_id: E-108
rule: /rules/code/code-2-fail-loudly.md
verdict: compliant
status: draft
tags: [errors, compensation, messaging]
example_file: src/CreateUserHandler.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T10:00:00Z }
sources:
  - id: evidence
    resource: hub-conn@src/connector-03/MessageFunctions.cs#L235-L343
---

# Situation

A handler creates an account in a directory, then assigns a manager and groups, publishes an event and sends mail.
If a later step fails, the account must not stay behind half set up.[^evidence]

# Why (verdict)

The catch block follows an order that keeps the failure visible: log the original exception first, so a failing
delete cannot replace it; try the compensation, by object id; log a failed compensation as its own error that says
manual cleanup is needed; and then `throw;`, because the earlier version swallowed the error and completed the
message. An error that is expected to happen at create time (duplicate name) is rethrown with the vendor's error
code in the log. This is the shape CODE.2 asks for: handled where something useful can be done (the undo), and
otherwise propagated.

# Compliant pattern

## Good example

```csharp
try
{
    await AssignAndPublishAsync(user, ct);
}
catch (Exception ex)
{
    logger.LogError(ex, "Creating {UserId} failed after the account existed", user.Id);   // cause first

    try
    {
        await directory.DeleteUserAsync(user.Id, ct);                                      // by id, not by name
    }
    catch (Exception rollbackEx)
    {
        logger.LogError(rollbackEx, "Rollback of {UserId} failed; manual cleanup needed", user.Id);
    }

    throw;                                                                                  // retry or dead-letter
}
```

## Bad example

```csharp
catch (Exception ex)
{
    await directory.DeleteUserAsync(user.Id, ct);   // if this throws, the original error is gone
    logger.LogInformation("Done");                  // and the message is completed as a success
}
```

# Not verified

The same handler swallows a failed manager lookup and a failed group assignment with a warning on purpose, and
mails a one-time password in plain text to a configured address. The first is a product decision not checked here;
the second is not covered by an existing rule (see the report).

[^evidence]: create, assign, publish, roll back
