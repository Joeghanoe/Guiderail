---
type: Example
title: "E-030 A configuration key is checked under one name and read under another"
description: The method validates that Gateway:OAuthScope is set and then reads OAuthScope, so the guard passes and the token request goes out with an empty scope; write each key once as a constant or bind an options class.
example_id: E-030
rule: /rules/code/code-4-write-a-name-once.md
verdict: violation
status: draft
tags: [configuration, naming, defect]
example_file: src/Services/TokenProvider.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T09:00:00Z }
---

# Situation

A method obtains an OAuth token. It first checks that `Gateway:OAuthUri` and `Gateway:OAuthScope` are configured and throws if not.
It then reads `Gateway:OAuthUri` again for the endpoint and reads `OAuthScope` (without the section) for the `resource` form field.

# Why (verdict)

The key `Gateway:OAuthScope` is written three times in different places and one of them lost its section. The guard checks the
right key, the request uses a different one, and the result is a token request with a null scope that fails or returns a
token for the wrong audience, while the code looks defensive. A name used in more than one place is written once (CODE.4):
a constant, or better an options class bound to the section and validated at start, so the key exists in one place and the
method receives a typed value.

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
