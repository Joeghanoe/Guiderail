---
type: Rule
title: "IAC.7 Per-environment values are configuration; everything fixed is written once in the pipeline"
description: Values that may differ per environment are parameters or variables.<env>.yml; names and fixed settings are written once in the pipeline with the environment name in them.
rule_id: IAC.7
principle: [/principles/p-04-metadata-before-configuration.md, /principles/p-05-reuse-before-reinvention.md]
tags: [iac, pipelines, configuration]
applies_to: ["**/*.yml", "**/*.yaml", "**/*.bicep", "**/*.bicepparam", "**/*.tf", "**/*.tfvars"]
enforced_by: [review]
severity: major
status: stable
---

# Rule

Every value lives in exactly one place, chosen by whether it can differ between environments:

| Kind of value | Where it lives | Examples |
| --- | --- | --- |
| May differ per environment (a configurable) | `variables/variables.<env>.yml`, or the pipeline's environment `parameters` when it must be known at compile time | subscription or project, SKU and sizing, retention, alert recipients, feature flags |
| Same everywhere, or derived from the environment name | once in the pipeline (`build-and-deploy.yml`, under `variables`), with `${{ environment.name }}` where the environment matters | resource names (IAC.6), tool versions, regions, tags |
| Secret | the variable group per environment, never a file | keys, passwords, client secrets |

- A name is a pattern written once (`orders-${{ environment.name }}-we-rg`), not a literal per environment file.
- Modules and templates take names and values as input and derive none; they carry no default that encodes an environment.
- A configurable may have the same value in every environment today (sizing that happens to match); it stays in `variables.<env>.yml` because it is allowed to differ. A value that can never differ belongs in the pipeline.

# Smells

- The same name repeated per stage or per environment file, differing only in `dev`/`prd`.
- A version, region or tag copied into every `variables.<env>.yml`.
- An environment literal (`-prd-`, a subscription ID) inside a module or a shared template.

# Central configuration convention

When the repository adopts the owner's central YAML configuration convention, use one configuration directory for shared values, environment values and resource names. E-044 records this newer convention; E-006 remains precedent for repositories with the earlier pipeline-owned naming layout. Do not silently migrate an established repository while fixing an unrelated issue.

- Top-level parameters represent choices for this run, such as forcing all services to deploy. Subscriptions, service connections, resource names, regions, SKUs and schedules are stable configuration, not an operator-facing environment object.
- Give operator-facing parameters concise `displayName` labels in the existing vocabulary and capitalization, for example `forceFullDeployment` with `Deploy All Services`. Missing labels alone are a minor usability finding. Internal template parameters need no UI label.
- Azure Pipelines loads a shared variable file, expands one stage definition using `split(variables.environments, ',')` and `each`, and loads environment and naming variable templates at stage or job scope. A naming template can take the environment identifier as a structural input. Configuration lives in the files even though the variables are scoped to stages.
- Repo-local job and step templates consume inherited runtime variables with `$(name)` rather than forwarding configuration through long parameter lists. Do not assume stage variables are visible through `${{ variables.name }}` during nested job-template expansion. Run choices and independent reusable template interfaces may still use explicit parameters.
- Bicep consumes names and values; it does not define a second naming policy or environment catalog. Generated parameter files may adapt the central YAML without becoming another manually maintained source.
- The ownership and reuse requirements also apply to GitHub Actions, but Azure's include and loop syntax does not. Explicit dependent jobs calling reusable deployment logic are valid. Do not force a matrix where promotion dependencies and environment approvals are clearer as jobs.
- Build IDs, artifact versions and deployment outputs are execution data, not static configuration. Secrets stay in the established secret store.
