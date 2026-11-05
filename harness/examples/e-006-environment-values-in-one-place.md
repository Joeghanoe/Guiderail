---
type: Example
title: "E-006 Environment values live in one place; fixed values are written once"
description: Organize environment-specific settings in dedicated variable files, and define common pipeline constants in one shared location.
example_id: E-006
rule: /rules/iac/iac-7-configuration-placement.md
verdict: violation
status: stable
verified: { by: human:teamvaluegroup, at: 2026-10-27T20:07:13Z }
tags: [pipelines, configuration]
example_file: pipelines/build-and-deploy.yml
eval_context_files: [variables/variables.dev.yml, variables/variables.prd.yml]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-19T00:00:00Z }
---

# Situation

A multi-stage pipeline repeats tool versions, naming rules, and configuration values across stages instead of extracting environment differences.

# Why (verdict)

Copying pipeline definitions across stages duplicates shared constants (tooling versions, naming schemas) and obscures which settings actually vary between environments (IAC.7). Isolate environment-specific values in `variables.<env>.yml` files and reference a single shared stage template.

# Compliant pattern

## Good example

```yaml
parameters:
  - name: environments
    type: object
    default:
      - name: dev
      - name: prd

variables:
  - name: bicepVersion                 # the same everywhere: written once
    value: "0.43.8"

stages:
  - ${{ each environment in parameters.environments }}:
      - stage: Deploy_${{ environment.name }}
        variables:
          - template: variables/variables.${{ environment.name }}.yml   # appServicePlanSku, retention
          - name: resourceGroupName                                       # a pattern, written once
            value: orders-${{ environment.name }}-we-rg
```

## Bad example

```yaml
stages:
  - stage: Deploy_dev
    variables:
      bicepVersion: "0.43.8"
      resourceGroupName: orders-dev-we-rg
      appServicePlanSku: B1
  - stage: Deploy_prd
    variables:
      bicepVersion: "0.43.8"
      resourceGroupName: orders-prd-we-rg
      appServicePlanSku: P1v3
```

# Variant: a module derives nothing and carries no environment

A template takes its values as parameters. It does not work them out of another name (that only works while the naming convention is followed, "which usually it is, until it is not"), and it does not carry a literal that belongs to one environment. A value that was hardcoded becomes a parameter with a default that suits every environment.

```bicep
// Good
param functionAppName string
param connectorName string = functionAppName          // explicit; the caller may override
param frequencyInSeconds int = 300
param healthPath string = '/health'

// Bad
param functionAppName string
var connectorName = replace(split(functionAppName, '-')[1], 'func', '')   // assumes the convention
var environment = 'dev'                                                   // typed by hand
var pingUrl = 'https://orders-dev-we-func.azurewebsites.net/health'       // one environment baked in
var frequencyInSeconds = 300                                              // cannot be changed by the caller
```

The same applies in the pipeline: an environment identifier typed in a job (`dev`) is the environment's name, and the job may need to be optional per environment through a variable.

# Not verified

Written for this example in neutral names. The variant comes from review feedback on a set of templates and pipelines; it follows IAC.7's bullet that modules derive no value and carry no environment default.
