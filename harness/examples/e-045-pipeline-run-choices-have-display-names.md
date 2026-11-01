---
type: Example
title: "E-045 Operator-facing pipeline choices have concise display names"
description: Operator-facing pipeline choices have concise display names.
example_id: E-045
rule: /rules/iac/iac-7-configuration-placement.md
verdict: violation
status: stable
verified: { by: human:joeghanoe, at: 2026-11-01T19:18:40Z }
tags: [feedback, regression]
generated: { by: codex/unknown, at: 2026-11-01T20:00:00Z }
example_file: azure-pipelines.yml
---

# Situation

A manual-run form must explain the choice in the repository's established vocabulary and capitalization. Keep parameter identifiers consistent with code conventions, and give at least top-level parameters concise displayName labels. Internal-only templates need no operator label. Missing labels are a minor usability finding.

## Good example

```yaml
parameters:
  - name: forceFullDeployment
    displayName: Deploy All Services
    type: boolean
    default: false
steps:
  - bash: echo "$FORCE_FULL_DEPLOYMENT"
    env:
      FORCE_FULL_DEPLOYMENT: ${{ parameters.forceFullDeployment }}
```

## Bad example

```yaml
parameters:
  - name: forceFullDeployment
    type: boolean
    default: false
steps:
  - bash: echo "$FORCE_FULL_DEPLOYMENT"
    env:
      FORCE_FULL_DEPLOYMENT: ${{ parameters.forceFullDeployment }}
```

# Evidence and limits

Prepared from the owner's feedback queue on 2026-11-01. Source snippets use neutral names. Model evaluation tests reviewer behavior, not execution of these snippets. The owner approved this example in the processing session on 2026-11-01. Approval concerns the expected reviewer behavior, not execution of the snippet.
