---
type: Gate
title: "Resolved Key Vault policy with PSRule (IAC.4 pilot)"
description: Selected upstream Key Vault policies evaluate offline expanded Bicep or ARM templates and supplied ARM parameters.
tool: harness/tools/verification/verify.py psrule, selected rules in tools/verification/tool-lock.json
owner: team:teamvalue-aicoe
status: stable
tags: [iac, azure, verification]
---

# Scope

The authoritative profile is `keyvault_rules` in the tool lock. PSRule for Azure supplies the actual rule definitions. Bicep compiles source; PSRule performs template and parameter expansion. No Azure login, deployment or custom property parser is involved. Required dependencies not available locally cause an error; Bicep does not restore modules during verification.

Consumer adoption is explicit through `keyVaultPilots` in the reusable PR template. Each entry identifies a Bicep or ARM template and optional ARM deployment parameters JSON. Fixtures test default and supplied values, missing properties, inactive resources, malformed source and no-vault applicability. No vault is not-applicable, not a policy pass.

# Overlap and residual review

After a successful resolved result, the legacy IaC gate skips its IAC.4 literal check only for that exact unchanged entry template. IAC.2/IAC.3, Terraform and other source paths keep their existing checks. Failed, missing and stale receipts do not suppress a legacy check. This avoids permanent duplicate enforcement while preserving uncovered paths.

The selected profile does not prove absence of access policies, narrow IAM grants, every resource's network/TLS policy or deployed state. These remain review concerns. Only supplied deployment inputs are covered; a different environment parameter set needs its own run.

# Evidence

Receipts preserve versions, source and parameter hashes, per-resource rule outcomes and explicit errors. Generated compiled-template content is removed after processing; its hash remains. Raw model output is never needed. Consumer branch protection and adoption remain repository-owned.
