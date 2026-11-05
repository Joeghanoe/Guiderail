---
type: Example
title: "E-044 Pipeline inputs are run choices and configuration has one owner"
description: Pipeline inputs are run choices and configuration has one owner.
example_id: E-044
rule: /rules/iac/iac-7-configuration-placement.md
verdict: violation
status: stable
verified: { by: human:teamvaluegroup, at: 2026-11-01T19:18:40Z }
tags: [feedback, regression]
generated: { by: codex/unknown, at: 2026-11-01T20:00:00Z }
eval_split_files: true
---

# Situation

The owner now requires a repo-owned configuration directory, including shared values, environment settings and resource names. Parameterized variable templates expand at stage scope; nested job templates use runtime macros for those values. Only run choices are top-level parameters, with clear display names. Internal environment template parameters are structural inputs, not UI choices. The owner manually confirmed the runtime pattern in the temporary Azure pipeline, including the corrected check. Compile-time visibility from the nested job template was unavailable and is not established by that success. [E-006](e-006-environment-values-in-one-place.md) is historical precedent for an older placement convention; this example records the newer explicitly adopted configuration-directory convention without rewriting E-006.

## Good example

```text
# File: azure-pipelines.yml
trigger: none
parameters:
  - name: forceFullDeployment
    displayName: Deploy All Services
    type: boolean
    default: false
variables:
  - template: deploy/variables/variables.shared.yml
stages:
  - ${{ each environment in split(variables.environments, ',') }}:
      - stage: Deploy_${{ environment }}
        variables:
          - template: deploy/variables/variables.${{ environment }}.yml
          - template: deploy/variables/variables.names.yml
            parameters:
              environment: ${{ environment }}
        jobs:
          - template: deploy/deploy.jobs.yml
            parameters:
              forceFullDeployment: ${{ parameters.forceFullDeployment }}
# File: deploy/variables/variables.shared.yml
variables:
  - name: environments
    value: dev
  - name: location
    value: westeurope
# File: deploy/variables/variables.dev.yml
variables:
  - name: subscription
    value: orders-development
# File: deploy/variables/variables.names.yml
parameters:
  - name: environment
    type: string
variables:
  - name: resourceGroupName
    value: orders-${{ parameters.environment }}-we-rg
# File: deploy/deploy.jobs.yml
parameters:
  - name: forceFullDeployment
    type: boolean
    default: false
jobs:
  - job: ValidateContext
    steps:
      - bash: echo "$RESOURCE_GROUP_NAME"
        env:
          RESOURCE_GROUP_NAME: $(resourceGroupName)
```

## Bad example

```text
# File: azure-pipelines.yml
parameters:
  - name: environments
    type: object
    default:
      - name: dev
        subscription: orders-development
        resourceGroupName: orders-dev-we-rg
        appServiceSku: B1
      - name: prd
        subscription: orders-production
        resourceGroupName: orders-prd-we-rg
        appServiceSku: P1v3
stages:
  - ${{ each environment in parameters.environments }}:
      - stage: Deploy_${{ environment.name }}
        jobs:
          - job: Deploy
            steps:
              - bash: echo "$RESOURCE_GROUP_NAME"
                env:
                  RESOURCE_GROUP_NAME: ${{ environment.resourceGroupName }}
```

# Evidence and limits

Prepared from the owner's feedback queue on 2026-11-01. Source snippets use neutral names. Model evaluation tests reviewer behavior, not execution of these snippets. The owner approved this example in the processing session on 2026-11-01. Approval concerns the expected reviewer behavior, not execution of the snippet.

# Related guidance

This example illustrates [IAC.7 Per-environment values are configuration; everything fixed is written once in the pipeline](../rules/iac/iac-7-configuration-placement.md). The `rule` metadata records the same relationship for tooling.
