# Gates

* [Banned API analyzer (T.2)](banned-api-analyzer.md) - Microsoft.CodeAnalysis.BannedApiAnalyzers with BannedSymbols.txt turns T.2 violations into build errors.
* [Harness pin check](harness-pin.md) - The PR pipeline fails when the harness checkout is not at the commit the repo's pipeline pins.
* [IaC settings check (IAC.2, IAC.3, IAC.4)](iac-settings.md) - check-iac.py fails a PR that sets a network default action to Allow, a TLS minimum below 1.2, or Key Vault soft delete, purge protection or RBAC authorization to false.
* [Private artifact check](private-artifacts.md) - The harness checkout contains no mined private review comments or raw evaluation outputs.
* [Scenario presence check (T.5)](scenario-presence.md) - check-scenarios.py fails a PR that changes a component without changing its scenarios or stating why not.
