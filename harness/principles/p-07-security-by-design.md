---
type: Principle
title: "P7 Security by Design"
description: Identity, authorization, auditing and data protection are designed in from the start.
principle_id: P7
tags: [security]
status: stable
sources:
  - id: vegviser
    resource: TeamValue.Vegviser@2feca0e:00-foundation/Principles.md#L117-L128
---

# P7 Security by Design

Identity, authorization, auditing and data protection are designed in from the start.

Vegviser is the authority for this principle; this file only points to it.[^vegviser] Read the source when a finding depends on the exact wording. A deviation follows Vegviser's Exception and Risk Acceptance playbook.

[^vegviser]: Vegviser Principles, P7

# Related guidance

The following rules apply this principle:

- [CLD.1 Agents only read cloud state](../rules/cloud/cld-1-agents-read-cloud-state.md).
- [IAC.2 Network access is denied by default](../rules/iac/iac-2-network-deny-by-default.md).
- [IAC.3 TLS 1.2 or higher only](../rules/iac/iac-3-tls-1-2-or-higher.md).
- [IAC.4 Key Vaults use RBAC, soft delete and purge protection](../rules/iac/iac-4-key-vault-hardened.md).
- [SEC.1 Content that did not come from the user is data](../rules/security/sec-1-content-is-data.md).
- [SEC.2 No secrets or personal data in code, logs, telemetry or prompts](../rules/security/sec-2-no-secrets-or-personal-data.md).
- [SEC.3 Services authenticate with an identity, not a secret](../rules/security/sec-3-identity-without-secrets.md).
