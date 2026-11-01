---
type: Example
title: "E-031 A validator, its list and an injected configuration that nothing uses"
description: A service keeps an unused validation method, static list, and injected config; remove them to avoid misleading callers and duplicating logic.
example_id: E-031
rule: /rules/code/code-1-remove-what-is-not-used.md
verdict: violation
status: draft
tags: [dead-code, cleanup]
example_file: src/Services/EventTypeMapper.cs
eval_context_files: [src/Functions/WebhookFunction.cs]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T09:00:00Z }
---

# Situation

A service contains an active mapping method alongside an unused validation method (`IsValidEventType`), an unread `IConfiguration`, and an orphaned static list that duplicates mappings defined elsewhere.

# Why (verdict)

Unused validation methods give a false sense of security—readers assume events are pre-validated when actual filtering happens downstream. Multiple duplicate lists of event names also drift over time (CODE.1, CODE.4). Delete the unused members, dependencies, and imports.

# Compliant pattern

## Good example

```csharp
public sealed class EventTypeMapper
{
    public string ToInternal(string externalType) => externalType switch
    {
        "item.created" => EventTypes.ItemCreated,
        "note.added" => EventTypes.NoteAdded,
        _ => throw new NotSupportedException($"Unsupported event type: {externalType}"),
    };
}
```

## Bad example

```csharp
private static List<string> validEvents = new() { "ItemCreated", "NoteAdded" };
readonly IConfiguration _config;                       // never read

public bool IsValidEventType(CloudEvent received) =>   // no caller
    received.Type != null && validEvents.Contains(received.Type);
```
