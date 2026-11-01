---
type: Example
title: "E-017 The wrapper refuses harmless az reads because their verb is not on a list"
description: The az branch allowed only a few read verbs, so monitoring and log commands were refused; it now allows everything except state-changing verbs and secret-returning reads.
example_id: E-017
rule: /rules/cloud/cld-1-agents-read-cloud-state.md
verdict: boundary
status: stable
verified: { by: human:joeghanoe, at: 2026-10-27T20:07:13Z }
tags: [cloud, az, wrapper, monitoring]
owner: human:joeghanoe
stale_after: 2027-04-20T00:00:00Z
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-20T00:00:00Z }
sources:
  - id: evidence
    resource: harness@tools/cloud/cloud-read.sh (az branch: the last word had to be show, list, get, query or exists)
  - id: requirement
    resource: the user wants every az read (list, show, monitoring, logs, metrics) and a block on create, update and delete
---

# Situation

`cloud-read.sh az ...` allowed a command only when its last word was a known read verb. Azure CLI has hundreds of command groups, and reads such as `az webapp log tail` or `az policy state summarize` end in a verb that is not on that list, so the agent was refused and the user ran the command by hand.[^evidence]

# Why (verdict)

CLD.1 holds: agents read, humans write, and secrets stay out. The boundary is how the wrapper decides. For `az`, the wrapper allows by default and refuses what changes state: create, update, delete, start, stop, deploy, assign, login and the like, as a word or the start of a compound (`delete-instances`), wherever the word stands in the arguments. Reads that name keys, secrets, credentials or tokens stay refused, and `az rest` stays GET only. The other CLIs keep their read-verb allowlist.

Consequence to accept: a denylist misses a state-changing verb nobody listed, and with the user's own login the wrapper is then the only barrier. Layer 1, a Reader identity in `HARNESS_AZURE_CONFIG_DIR`, remains the real boundary; add the missed verb to the list and a test when you find one.

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
