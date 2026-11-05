---
type: Example
title: "E-017 The wrapper refuses harmless az reads because their verb is not on a list"
description: The az wrapper permits diagnostic and query commands by default, blocking only mutating verbs and secret retrieval.
example_id: E-017
rule: /rules/cloud/cld-1-agents-read-cloud-state.md
verdict: boundary
status: stable
verified: { by: human:teamvaluegroup, at: 2026-10-27T20:07:13Z }
tags: [cloud, az, wrapper, monitoring]
owner: human:teamvaluegroup
stale_after: 2027-04-20T00:00:00Z
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-20T00:00:00Z }
sources:
  - id: evidence
    resource: harness@tools/cloud/cloud-read.sh (az branch: the last word had to be show, list, get, query or exists)
  - id: requirement
    resource: the user wants every az read (list, show, monitoring, logs, metrics) and a block on create, update and delete
---

# Situation

`cloud-read.sh az ...` previously required commands to end in an explicit read verb. Legitimate diagnostic commands like `az webapp log tail` or `az policy state summarize` were blocked simply because their subcommands were not on the strict allowlist.[^evidence]

# Why (verdict)

[CLD.1](../rules/cloud/cld-1-agents-read-cloud-state.md) ensures agents read while write privileges remain strictly with developers. Because Azure CLI has hundreds of subcommands, the wrapper permits diagnostic queries by default while actively blocking mutating verbs (create, delete, update, deploy, assign, start, stop) and secret-exposing operations (keys, secrets, credentials).

## Good example

```bash
~/.golden-path-harness/harness/tools/cloud/cloud-read.sh az monitor metrics list --resource <id> --metric Requests
~/.golden-path-harness/harness/tools/cloud/cloud-read.sh az webapp log tail -n <app> -g <rg>
```

## Bad example

```bash
# refused (exit 3), also with options first: az --subscription <id> group delete
~/.golden-path-harness/harness/tools/cloud/cloud-read.sh az group delete -n rg-dev
```

# Not verified

Tested with stubs only, not against a real `az` login.

[^evidence]: wrapper refusal, exit code 3
