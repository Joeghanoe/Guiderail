---
type: Example
title: "E-015 The read-only cloud wrapper cannot read with the user's own login, even when the user says the agent may read"
description: The cloud wrapper allows an agent to read logs using the developer's existing Azure login when explicitly granted, rather than blocking on a missing dedicated reader account.
example_id: E-015
rule: /rules/cloud/cld-1-agents-read-cloud-state.md
verdict: boundary
status: stable
verified: { by: human:joeghanoe, at: 2026-10-27T20:07:13Z }
tags: [cloud, az, wrapper, identity]
owner: human:joeghanoe
stale_after: 2027-04-19T00:00:00Z
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-19T00:00:00Z }
sources:
  - id: evidence
    resource: harness@tools/cloud/cloud-read.sh (az branch: HARNESS_AZURE_CONFIG_DIR must be set)
  - id: requirement
    resource: the user explicitly allows reads for this session and does the login themselves
---

# Situation

An agent needs to inspect dev gateway logs to troubleshoot a failed load test. The developer already ran `az login` and authorized the read, but [cloud-read.sh](../tools/cloud/cloud-read.sh) failed because a dedicated reader config directory was not configured, forcing manual copy-pasting.[^evidence]

# Why (verdict)

CLD.1 requires that agents only read and never manage credentials or execute writes. When a developer does not have a dedicated read-only service principal set up, their active `az login` acts as the explicit grant. The wrapper falls back to this session for read verbs (show, list, query, logs) while strictly enforcing read-only protections in layer 2. Agents never run login commands, switch accounts, or execute mutations.

## Good example

```bash
# the user did `az login`; the agent reads for diagnosis
~/.golden-path-harness/harness/tools/cloud/cloud-read.sh az monitor log-analytics query -w <workspace> -a "<query>"
```

## Bad example

```bash
# a write verb through the wrapper is refused (exit 3), whoever is logged in
~/.golden-path-harness/harness/tools/cloud/cloud-read.sh az group delete -n rg-dev
```

# Not verified

Tested with stubs only, not against a real `az` login. `az monitor log-analytics query` passes the read-verb check (tested with a stub).

[^evidence]: wrapper refusal, exit code 3
