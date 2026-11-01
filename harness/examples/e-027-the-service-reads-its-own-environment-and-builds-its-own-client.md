---
type: Example
title: "E-027 A service builds its own HttpClient and reads environment variables next to the injected factory"
description: A service uses an injected factory for token requests but manually instantiates HttpClient for API calls; register a typed client so all HTTP calls are managed centrally.
example_id: E-027
rule: /rules/testing/t-2-services-do-not-create-io.md
verdict: violation
status: draft
tags: [testability, http, dependency-injection]
example_file: src/Services/ExternalApiClient.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T09:00:00Z }
---

# Situation

An API client uses `IHttpClientFactory` to retrieve an auth token, but then spins up a manual `new HttpClient()` for business calls and reads settings directly via `Environment.GetEnvironmentVariable`.

# Why (verdict)

Instantiating `HttpClient` manually bypasses connection pooling and makes core business methods untestable without contacting live external endpoints (T.2). Reading environment variables inside methods also scatters configuration throughout the codebase. Configure typed HTTP clients and bind validated options at startup in the composition root.

# Compliant pattern

## Good example

```csharp
// Program.cs
services.AddHttpClient<ExternalApiClient>((sp, client) =>
{
    var opts = sp.GetRequiredService<IOptions<ExternalApiOptions>>().Value;
    client.BaseAddress = new Uri(opts.BaseUrl);
});

// ExternalApiClient.cs
public sealed class ExternalApiClient(HttpClient http, ITokenSource tokens)
{
    public async Task<string> GetAsync(string path, CancellationToken ct)
    {
        using var request = new HttpRequestMessage(HttpMethod.Get, path);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", await tokens.GetAsync(ct));
        using var response = await http.SendAsync(request, ct);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsStringAsync(ct);
    }
}
```

## Bad example

```csharp
private async Task<HttpClient> GetHttpClient()
{
    var token = await GetToken();             // uses _httpClientFactory.CreateClient()
    var httpClient = new HttpClient();        // the call that matters is not injectable
    httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
    return httpClient;
}

var nameKey = Environment.GetEnvironmentVariable("ClientCertificateNameKey");
```
