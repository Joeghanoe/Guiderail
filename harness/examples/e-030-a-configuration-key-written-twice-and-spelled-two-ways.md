---
type: Example
title: "E-030 A configuration key is checked under one name and read under another"
description: A method validates a configuration key with its section prefix but reads it without it, causing silent authentication failures; define config keys once or bind an options class.
example_id: E-030
rule: /rules/code/code-4-write-a-name-once.md
verdict: violation
status: stable
verified: { by: human:joeghanoe, at: 2026-11-01T19:28:57Z }
tags: [configuration, naming, defect]
example_file: src/Services/TokenProvider.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T09:00:00Z }
---

# Situation

A method fetches an OAuth token by checking that `Gateway:OAuthUri` and `Gateway:OAuthScope` exist. When constructing the request payload, it accidentally reads `OAuthScope` without the `Gateway:` prefix, passing a null or empty value.

# Why (verdict)

String-based configuration keys drift easily when repeated across guards and callers. Here, the guard checks the prefixed key while the payload reads the un-prefixed key, silently sending an invalid token request (CODE.4). Bind settings to a strongly-typed options class at startup or define the key as a shared constant.

# Compliant pattern

## Good example

```csharp
public sealed class TokenOptions
{
    [Required] public string OAuthUri { get; init; } = "";
    [Required] public string OAuthScope { get; init; } = "";
}

// Program.cs
services.AddOptions<TokenOptions>().BindConfiguration("Gateway").ValidateDataAnnotations().ValidateOnStart();

// service
var form = new FormUrlEncodedContent(new Dictionary<string, string>
{
    ["grant_type"] = "client_credentials",
    ["resource"] = options.Value.OAuthScope,
});
```

## Bad example

```csharp
if (string.IsNullOrWhiteSpace(_config["Gateway:OAuthScope"])) throw new ArgumentException("Gateway:OAuthScope is not configured");
var content = new FormUrlEncodedContent([
    new KeyValuePair<string, string>("resource", _config["OAuthScope"]),   // not the key that was checked
]);
```
