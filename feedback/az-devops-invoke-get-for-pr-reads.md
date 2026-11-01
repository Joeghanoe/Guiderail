---
type: Example
title: "C-NNN Cloud read access should not depend on a special Azure CLI config directory"
description: Azure read commands use the user's current CLI login, while command-level wrapper rules decide what is allowed.
example_id: C-NNN
rule: /rules/cloud/cld-1-agents-read-cloud-state.md
verdict: open
status: draft
tags: [cloud, azure-devops, wrapper]
generated: { by: copilot-sdk/unknown, at: 2026-10-21T11:35:01Z }
sources:
  - id: evidence
    resource: harness/tools/cloud/cloud-read.sh (az rest requires HARNESS_AZURE_CONFIG_DIR; az can override AZURE_CONFIG_DIR)
  - id: other-wrapper
    resource: harness/tools/azure-devops/ado-common.sh (conditionally sets AZURE_CONFIG_DIR from HARNESS_AZURE_CONFIG_DIR)
  - id: precedent
    resource: harness/examples/e-015-user-granted-current-login.md (the user's own login is accepted when no separate reader is configured)
---

# Situation

Azure read access has an unnecessary second identity/configuration path. `cloud-read.sh` uses the user's normal Azure CLI login for most `az` commands, but refuses `az rest` unless `HARNESS_AZURE_CONFIG_DIR` is set; when set, it redirects the CLI to that directory. The Azure DevOps read helpers also conditionally redirect to it. This makes the same read-only command policy depend on whether an environment variable is configured, and requires a separate login setup even when the user has already logged in and granted the agent permission to read.

The initial symptom was reading pull-request comments: `az devops invoke` is blocked because `invoke` is in the mutating-verb list, while `az rest --method get` is blocked by the config-directory requirement. The underlying issue is broader than either command: identity setup and command authorization are coupled when they should be independent.

# Why (verdict)

Adopted. Command authorization is decided from the command (HTTP method and arguments), not from a required configuration directory:

1. `cloud-read.sh` permits `az rest` with `--method get` using the user's current Azure login without requiring `HARNESS_AZURE_CONFIG_DIR`.
2. `cloud-read.sh` permits `az devops invoke` for GET/HEAD/OPTIONS requests without an `--in-file` payload.
3. Dedicated helper `harness/tools/azure-devops/ado-pr-threads.sh` provides formatted PR comment and resolution status.

## Implemented change

- Removed the `HARNESS_AZURE_CONFIG_DIR` requirement for `az rest` in `cloud-read.sh`. `az rest` requires `--method get`.
- Permitted `az devops invoke` in `cloud-read.sh` when using read methods (GET, HEAD, OPTIONS or default GET) and no `--in-file`.
- Created `harness/tools/azure-devops/ado-pr-threads.sh` to read and parse PR comment threads and resolution status.
- Added test coverage in `tests/run.sh` covering `az rest GET`, `az devops invoke GET`, and `ado-pr-threads.sh`.

# Not verified

The precise read-only Azure DevOps resources and whether omitting `--http-method` reliably means GET need verification before permitting any `invoke` form. The denylist's known blind spots also remain: removing the config-directory requirement deliberately leaves layer 2 as the only restriction when the user's current identity has write permissions.
