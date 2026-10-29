---
type: Case
title: "C-015 The read-only cloud wrapper cannot read with the user's own login, even when the user says the agent may read"
description: The wrapper refuses every az read unless a separate reader identity is configured, so an agent cannot read logs the user already allowed it to read.
case_id: C-015
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

An agent had to read gateway logs on DEV to explain a failed load test. The user had logged in with `az login`
(default config directory) and said the agent may read. `cloud-read.sh az ...` still exited with
`HARNESS_AZURE_CONFIG_DIR is not set; az would use your personal login`. The only way forward was a one-time
setup of a separate reader account, or the user running every query and pasting the result.[^evidence]

# Why (verdict)

CLD.1 holds: agents never log in or switch accounts, and writes stay with humans. The wrapper's layer 1
(a read-only identity) is the real boundary, but the user has no separate reader account here and does not
want to maintain one. Boundary: the login the user did themselves is the grant. Without a separate reader configured, `cloud-read.sh` uses the login the user did
themselves, with no extra step; the user only intervenes to log in, and to run anything that creates, updates
or deletes. Everything else in layer 2 stays: read verbs only (show, list, get, query, logs), no secrets, no
`login`, `account set` or `config`, `az rest` only with GET. The agent never logs in, switches accounts or
sets the config directory. Consequence to accept: with a personal login, layer 1 no longer guarantees
read-only, so layer 2 alone carries that.

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

Tested with stubs only, not against a real `az` login. `az monitor log-analytics query` passes the read-verb
check (tested with a stub).

[^evidence]: wrapper refusal, exit code 3
