---
type: Example
title: "E-028 Integration configuration is deserialised and validated once, and a bad entry fails by name"
description: A base provider reads one JSON configuration per integration, rejects an empty or unparsable entry, and asks the subclass to validate the mandatory fields; the error names the field, never the value.
example_id: E-028
rule: /rules/code/code-2-fail-loudly.md
verdict: compliant
status: draft
tags: [configuration, validation, errors]
example_file: src/Configuration/IntegrationConfigurationProvider.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T09:00:00Z }
---

# Situation

Each external integration has its own settings stored as one JSON document per integration in a vault. An abstract base class
loads the document by integration id, deserialises it and calls an abstract `ValidateConfig()` that each implementation provides.

# Why (verdict)

A missing document, an unparsable document and a missing mandatory field each throw `InvalidOperationException` or
`ArgumentException` with the integration id or the field name. The service never starts a call with a half-filled
configuration, so the failure shows up on the first message for that integration and names what is missing (CODE.2). The log
lines carry the integration id and the field name only, not the document, which is the right amount of detail with credentials
inside the document (SEC.2). Adding an integration is one subclass with its own validation.

Two things to improve if copying: the rethrown `InvalidOperationException` for a missing field repeats the "failed to
deserialize" message and drops the field name, and the original exception is not passed as the inner exception.

# Compliant pattern

## Good example

```csharp
public abstract class IntegrationConfigurationProvider<T> where T : IntegrationConfiguration
{
    public T Configuration { get; }

    protected IntegrationConfigurationProvider(IConfiguration source, ILogger logger, string integrationId)
    {
        var json = source[$"{integrationId}-configuration"];
        if (string.IsNullOrEmpty(json))
        {
            throw new InvalidOperationException($"Configuration for integration {integrationId} is missing or empty");
        }

        try { Configuration = JsonConvert.DeserializeObject<T>(json) ?? throw new JsonException("null"); }
        catch (JsonException ex)
        {
            throw new InvalidOperationException($"Configuration for integration {integrationId} cannot be read", ex);
        }

        try { Validate(); }
        catch (ArgumentException ex)
        {
            throw new InvalidOperationException($"Configuration for integration {integrationId} lacks {ex.Message}", ex);
        }
    }

    protected abstract void Validate();   // throw ArgumentException(fieldName) for a missing mandatory field
}
```

## Bad example

```csharp
var json = source[$"{integrationId}-configuration"];
Configuration = JsonConvert.DeserializeObject<T>(json);   // null on empty, NullReferenceException on first use
```
