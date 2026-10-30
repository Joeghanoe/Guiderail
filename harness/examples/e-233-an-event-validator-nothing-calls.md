---
type: Example
title: "E-233 A validator, its list and an injected configuration that nothing uses"
description: A service keeps an event-type list, a validation method and an injected configuration that no caller reads; delete them and the using directives that came with them.
example_id: E-233
rule: /rules/code/code-1-remove-what-is-not-used.md
verdict: violation
status: draft
tags: [dead-code, cleanup]
example_file: src/Services/WebhookService.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T09:00:00Z }
sources:
  - id: evidence
    resource: b2b-hook@Services/WebhookService.cs#L8-L43
---

# Situation

A small service holds two methods. `GetEventType` maps the partner's event names to internal ones and is used. The second,
`IsValidEventType`, checks a static list of internal names against a cloud-event type, and nothing in the project calls it;
the injected `IConfiguration` is stored and never read. The list duplicates the `switch` in the first method and the
`switch` in the function that consumes it.[^evidence]

# Why (verdict)

The unused validator looks like a guard, so a reader assumes unknown events are already filtered, and they are not: the
real check is the default arm of a `switch` elsewhere. A fourth copy of the event names is one more place to forget when a
type is added (CODE.1, and CODE.4 for the names). Remove the method, the list, the field, the constructor parameter and the
`using` that only served them; the compiler's unused-member analysers do not flag public members, so a reviewer has to.

# Compliant pattern

## Good example

```csharp
public sealed class EventTypeMapper
{
    public string ToInternal(string partnerType) => partnerType switch
    {
        "ticket.created" => EventTypes.CaseCreated,
        "comment.created" => EventTypes.CommentCreated,
        _ => throw new NotSupportedException($"Unsupported event type: {partnerType}"),
    };
}
```

## Bad example

```csharp
private static List<string> validEvents = new() { "CaseCreated", "CommentCreated" };
readonly IConfiguration _config;                       // never read

public bool IsValidEventType(CloudEvent received) =>   // no caller
    received.Type != null && validEvents.Contains(received.Type);
```

# Not verified

Searched the project for callers with grep; a reflection or external caller would not show up there.

[^evidence]: Event-type service of a webhook-to-case function app.
