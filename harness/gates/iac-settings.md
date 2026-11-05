---
type: Gate
title: "IaC settings check (IAC.2, IAC.3, IAC.4)"
description: check-iac.py fails a PR that sets a network default action to Allow, a TLS minimum below 1.2, or Key Vault soft delete, purge protection or RBAC authorization to false.
tool: harness/tools/iac/check-iac.py
owner: team:teamvalue-aicoe
status: stable
tags: [iac, security]
---

# Coverage

Changed `.bicep` and `.tf` files, one explicit wrong value per line. Only a setting that is written down is found.

# Blind spots

A setting that is missing (the platform default applies), values that come from a variable or parameter, other file types such as ARM JSON, and whether a public entry point is justified (that is review).

# Complementary checks

AI review of [IAC.2](../rules/iac/iac-2-network-deny-by-default.md) to [IAC.4](../rules/iac/iac-4-key-vault-hardened.md) for what the script cannot see.

# Failure behaviour

Exit 1 with `path:line: rule message`; the PR step fails.

# Exception route

A PR description line `iac: n/a - <reason>` (at least 10 characters), visible to the reviewer.

# Refresh trigger

A new resource type with its own spelling of these settings, or a change to [IAC.2](../rules/iac/iac-2-network-deny-by-default.md), [IAC.3](../rules/iac/iac-3-tls-1-2-or-higher.md) or IAC.4.
