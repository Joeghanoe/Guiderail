---
type: Example
title: "E-028 Integration configuration is deserialised and validated once, and a bad entry fails by name"
description: A base provider loads and validates integration settings upfront, failing loudly on missing fields while keeping sensitive values out of error messages.
example_id: E-028
rule: /rules/code/code-2-fail-loudly.md
eval_bad_rule_id: CODE.6
verdict: compliant
status: stable
verified: { by: human:joeghanoe, at: 2026-11-01T19:28:57Z }
tags: [configuration, validation, errors]
example_file: src/Configuration/IntegrationConfigurationProvider.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T09:00:00Z }
---

# Situation

An abstract base class loads external integration settings stored as JSON documents in a vault, deserializes them, and calls a type-specific `ValidateConfig()` hook.

# Why (verdict)

Missing or malformed configuration documents should fail immediately with an explicit error naming the missing property, preventing partially configured services from running (CODE.2). Error messages and logs should name only the integration ID and key name, keeping secret values out of logs (SEC.2).

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
