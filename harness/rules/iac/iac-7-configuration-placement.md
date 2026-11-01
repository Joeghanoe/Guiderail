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
