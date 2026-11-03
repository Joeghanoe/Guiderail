---
type: Example
title: "E-050 A resource named like a verb is data, and the wrapper holds no default org or subscription"
description: The az wrapper judges the command words, not option values, and subscription and organization are passed on each call.
example_id: E-050
rule: /rules/cloud/cld-1-agents-read-cloud-state.md
verdict: boundary
status: draft
tags: [cloud, az, wrapper, apim, azure-devops]
owner: human:joeghanoe
stale_after: 2027-05-03T00:00:00Z
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-11-03T00:00:00Z }
sources:
  - id: evidence
    resource: harness@tools/cloud/cloud-read.sh (every non-option word was checked against the state-changing verbs, so --resource-group set-rg and --service-name publish-apim were refused)
  - id: requirement
    resource: the user sees lookups on another subscription fail and the agent take another route
---

# Situation

E-017 made `az` reads allowed by default and refused state-changing verbs. The check looked at every word that was not an option, including the value of an option, so a resource group `set-rg` or an API Management service `publish-apim` was refused as "changes state".[^evidence] `az account set`, `az extension add` and `az devops configure` are refused by design (CLD.1), so a lookup on a subscription or organization that is not selected has to name it on the call. Without that written down the agent improvised another route.

# Why (verdict)

The verb is the command, not the name of the thing it acts on. The wrapper keeps refusing a verb in the command path, after a global option (`az --subscription x group delete`) and as an exact option value (`--unknown-flag delete`). It stops refusing a name that merely starts like a verb. `az devops configure` is refused because it rewrites local defaults. Federated credentials are issuer and subject metadata, not a secret.

## Good example

```bash
~/.golden-path-harness/harness/tools/cloud/cloud-read.sh az apim api list --subscription <id> --resource-group set-rg --service-name publish-apim
~/.golden-path-harness/harness/tools/cloud/cloud-read.sh az repos pr list --org https://dev.azure.com/<org> --project <project>
```

## Bad example

```bash
# refused (exit 3): the verb is in the command path, wherever the options stand
~/.golden-path-harness/harness/tools/cloud/cloud-read.sh az --subscription <id> group delete -n rg-dev
# refused (exit 3): rewrites the user's local az devops defaults
~/.golden-path-harness/harness/tools/cloud/cloud-read.sh az devops configure -d organization=https://dev.azure.com/<org>
```

# Not verified

Tested with stubs only (`tests/run.sh`, cloud-read section), not against a real `az` login.

[^evidence]: wrapper refusal, exit code 3
