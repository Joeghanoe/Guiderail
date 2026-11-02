# Rules

* [IAC.1 Diagnostics are proportionate: the audit trail always, the rest when something uses it](iac-1-proportionate-diagnostics.md) - Every resource keeps its audit logs; verbose logs and metric export are added only for a named consumer, sent to the cheapest destination that serves it.
* [IAC.2 Network access is denied by default](iac-2-network-deny-by-default.md) - Network ACLs default to Deny with bypass for platform services; public access is off unless the resource is meant to be public.
* [IAC.3 TLS 1.2 or higher only](iac-3-tls-1-2-or-higher.md) - Minimum TLS 1.2 on every endpoint; TLS 1.0/1.1, SSL 3.0, CBC and TripleDES are off.
* [IAC.4 Key Vaults use RBAC, soft delete and purge protection](iac-4-key-vault-hardened.md) - Key Vaults set enableRbacAuthorization, enableSoftDelete and enablePurgeProtection to true.
* [IAC.5 Every resource is declared in code](iac-5-everything-in-code.md) - Resources exist only through Bicep or Terraform; nothing is created by hand in a portal or console.
* [IAC.6 New resources follow the TeamValue naming convention, or the repo's own](iac-6-naming-convention.md) - New resource names follow {workload}[-{component}]-{env}-{region}-{type} in kebab-example, unless the repo already has an established convention, which then wins.
* [IAC.7 Per-environment values are configuration; everything fixed is written once in the pipeline](iac-7-configuration-placement.md) - Values that may differ per environment are parameters or variables.<env>.yml; names and fixed settings are written once in the pipeline with the environment name in them.
* [IAC.8 Pipelines call scripts; they do not contain them](iac-8-pipelines-call-scripts.md) - Anything longer than a line or two is a script file in the repo that can be run and tested locally, and the pipeline step calls it.
