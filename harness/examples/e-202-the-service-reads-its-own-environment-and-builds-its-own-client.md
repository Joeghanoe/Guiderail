---
type: Example
title: "E-202 A service builds its own HttpClient and reads environment variables next to the injected factory"
description: One method asks the injected factory for a client for the token call and then news up a bare HttpClient for the real call; register a named or typed client and let the factory own every call.
example_id: E-202
rule: /rules/testing/t-2-services-do-not-create-io.md
verdict: violation
status: draft
tags: [testability, http, dependency-injection]
example_file: src/Services/PartnerService.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T09:00:00Z }
sources:
  - id: evidence
    resource: b2b-ext@Services/ThirdParty/PartnerA/PartnerAService.cs#L236-L250
  - id: evidence-env
    resource: b2b-ext@Services/ThirdParty/Shared/CertificateService.cs#L26-L36
---

# Situation

A partner service already receives `IHttpClientFactory` and uses it to fetch an OAuth token. For the actual calls, a helper
creates `new HttpClient()` and sets the bearer header on it. A sibling service reads `Environment.GetEnvironmentVariable`
three times inside a method to find the names of its settings.[^evidence]

# Why (verdict)

The token call can be stubbed with a handler, the business call cannot: it goes to the real endpoint, so the method that
matters is untestable without the partner. A bare `new HttpClient()` per call also exhausts sockets under load, and the
commented-out lines above it show someone already tried to add a client certificate there and gave up because the
handler cannot be configured by hand and tested (T.2). Environment access moves to the composition root, where an
options class is bound and validated once. The service takes `HttpClient` or `IOptions<T>` and nothing else.

# Compliant pattern

## Good example

```csharp
// Program.cs
services.AddHttpClient<PartnerClient>((sp, client) =>
{
    var opts = sp.GetRequiredService<IOptions<PartnerOptions>>().Value;
    client.BaseAddress = new Uri(opts.BaseUrl);
});

// PartnerClient.cs
public sealed class PartnerClient(HttpClient http, ITokenSource tokens)
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

# Not verified

Not run. The banned-API analyzer from the repo template would flag both constructs; the source repo does not use it.

[^evidence]: Partner service and certificate service of a case-sync function app.
