---
type: Example
title: "E-201 A credential loader logs key names, secret lengths and stack traces"
description: A certificate loader writes the vault key names, the passphrase length and the exception details to the log at Information level; log that a load succeeded or failed, with the key name at most, and nothing about the secret.
example_id: E-201
rule: /rules/security/sec-2-no-secrets-or-personal-data.md
verdict: violation
status: draft
tags: [secrets, logging, certificates]
example_file: src/Services/CertificateService.cs
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-30T09:00:00Z }
sources:
  - id: evidence
    resource: b2b-ext@Services/ThirdParty/Shared/CertificateService.cs#L23-L65
---

# Situation

A service loads a client certificate and its passphrase from configuration (backed by a vault) so it can sign requests to a
partner. While debugging a bad deployment someone added a log line for every step.[^evidence]

# Why (verdict)

The log now carries the names of the vault entries holding the certificate and its passphrase, the length of the
passphrase, the exception message, the inner exception message and the full stack trace, all at Information level, which
production keeps. A passphrase length shortens a brute-force search, the key names tell an attacker where to look,
and exception text from a parsing failure can echo input (SEC.2). The `throw e;` also resets the stack trace. A loader needs
two log lines: what it is loading (a logical name) and whether that worked. Failure is thrown with a message that names the
missing setting, not its value (CODE.2).

# Compliant pattern

## Good example

```csharp
public sealed class ClientCertificateProvider(IOptions<CertificateOptions> options, ILogger<ClientCertificateProvider> logger)
{
    public X509Certificate2 Load()
    {
        var settings = options.Value;   // validated at start: both values present
        try
        {
            var cert = new X509Certificate2(Convert.FromBase64String(settings.PfxBase64), settings.Passphrase);
            logger.LogInformation("Client certificate loaded, expires {NotAfter:O}", cert.NotAfter);
            return cert;
        }
        catch (CryptographicException ex)
        {
            throw new InvalidOperationException("The client certificate could not be loaded; check the vault entry.", ex);
        }
    }
}
```

## Bad example

```csharp
_logger.LogInformation($"Certificate name key: {certificateKeyName}");
_logger.LogInformation($"Certificate password key: {passphraseKeyName}");
_logger.LogInformation($"Certificate Passphrase Length: {passphrase.Length}");
try
{
    return new X509Certificate2(certificateBytes, passphrase);
}
catch (Exception e)
{
    _logger.LogError(e, "Error while loading certificate");
    _logger.LogInformation($"Exception: {e.Message}");
    _logger.LogInformation($"Inner Exception: {e?.InnerException?.Message}");
    _logger.LogInformation(e.StackTrace);
    throw e;
}
```

# Not verified

Not run. Whether the log sink is access-controlled was not checked; the rule applies either way.

[^evidence]: Certificate service of a case-sync function app.
