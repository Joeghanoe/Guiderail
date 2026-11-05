---
type: Rule
title: "CLD.1 Agents only read cloud state"
description: Agents use cloud CLIs and APIs read-only, through the wrapper, with a read-only identity.
rule_id: CLD.1
principle: [/principles/p-03-governed-autonomy.md, /principles/p-07-security-by-design.md]
tags: [cloud, azure, tcloud, safety]
applies_to: ["**"]
enforced_by: [identity, tool:cloud-read, hook:guard-bash]
severity: blocker
status: stable
---

# Rule

An agent reads Azure, T Cloud, Azure DevOps and Kubernetes state; it never changes it. A change is written down as a command for a human to run.

Logging in is always done by the user: `az login`, `az account set`, `kubectl config use-context`, `hcloud configure` and every other login or account switch. An agent never logs in, logs out or switches the account or subscription a CLI uses; [cloud-read.sh](../../tools/cloud/cloud-read.sh) and the hooks refuse it.

# Layers

| Layer | What | Hard or soft |
| --- | --- | --- |
| 1. Identity | The agent's CLI uses its own login: Azure `Reader` without data-plane roles, a T Cloud user with only read policies, an Azure DevOps PAT with read scopes. Locally: a separate `AZURE_CONFIG_DIR`, so the agent never sees your Owner token | **Hard**: the real boundary |
| 2. Wrapper | [cloud-read.sh](../../tools/cloud/cloud-read.sh): for `az`, everything except state-changing verbs (create, update, delete, ...) and secret-returning reads, so monitoring, logs and metrics work (E-017); for the other CLIs, read verbs only | Hard for what goes through it |
| 3. Hooks | [guard-bash.sh](../../hooks/guard-bash.sh) blocks cloud CLIs, cloud management URLs and Az write cmdlets outside the wrapper | Guardrail |
| 4. Instructions | This rule | Soft |

If layer 1 is wrong, the other three only look safe.

# Reads that return secrets are writes

`Reader` already lacks `listKeys`, but the wrapper also refuses anything that names keys, secrets, credentials, tokens, SAS, connection strings or publishing profiles, even when it is a `list` or `show`: `az storage account keys list`, `az keyvault secret show`, `az account get-access-token` and `kubectl get secret` are refused. `az keyvault list` (vault names) is allowed.

# Boundary

Without a separate reader account, the login the user did themselves is the grant: the wrapper reads (show, list, get, query, logs) with it and needs no further step (E-015). The agent still never logs in, switches accounts or sets the config directory ([guard-bash.sh](../../hooks/guard-bash.sh) blocks it). Layer 1 then no longer guarantees read-only, so the wrapper's verb and secret checks alone carry it.

Tests in a DEV environment write (a backup run, an incident in ServiceNow). They run under the pipeline's identity, not the agent's. The agent reads their results.
