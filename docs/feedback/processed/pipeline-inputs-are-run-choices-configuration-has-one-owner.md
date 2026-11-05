---
type: Example
title: "C-NNN Pipeline inputs are run choices; configuration has one owner"
description: Keep deployment configuration and resource names in one repo-owned YAML location, with reusable deployment logic and platform-specific orchestration.
example_id: C-NNN
rule: /rules/iac/iac-7-configuration-placement.md
verdict: open
status: processed
tags: [pipelines, configuration, azure-pipelines, github-actions, bicep]
generated: { by: codex/unknown, at: 2026-11-01T18:40:57Z }
sources:
  - id: evidence
    resource: repo owner feedback in this session, 2026-11-01; deployment pipeline, variable-template and Bicep examples, followed by cross-platform scope clarification
---

# Situation

A deployment pipeline exposes an environment configuration object as queue-time parameters. It contains subscriptions, service connections, network ranges, schedules and resource settings. Resource names are defined elsewhere in pipeline stages or derived in Bicep functions. A second implementation moves environment configuration to YAML variable templates but duplicates stage definitions and continues to pass configuration through long template parameter lists.

The owner requests a central repo-owned location for configuration, including resource names. The owner clarifies that the underlying convention applies to both Azure Pipelines and GitHub Actions: inputs represent run choices, configuration has one owner, and deployment logic is reusable. The requested Azure Pipelines implementation uses a top-level `environments` variable, splits it, and expands one stage definition with `each`.

# Why (verdict)

This is a proposed replacement for part of IAC.7, not a violation under its current wording. IAC.7 currently places fixed values and name patterns in pipeline variables and permits compile-time environment configuration in parameters. Human-verified E-006 demonstrates both choices. This draft preserves that precedent and records the requested change for review; it does not silently override it.

The proposed convention optimizes for finding and reviewing configuration in one predictable directory. It accepts explicit per-environment values or centrally defined naming expressions in exchange for keeping naming policy out of orchestration and infrastructure modules. Centralization means one authoritative definition per value, not one giant file or a second configuration copy in every tool's native format.

# Proposed guidance

- Entry-point parameters and manually dispatched workflow inputs represent choices for this run, such as `forceFullDeployment`. Stable subscriptions, resource names, regions, service connections, SKUs, schedules, endpoint URLs and environment defaults belong in configuration files.
- Give every operator-facing parameter a clear, concise display name, at least at the pipeline entry point. Describe the action or choice in the UI, for example `forceFullDeployment` becomes `Deploy All Services`. Follow the repository's existing conventions for parameter identifiers, capitalization and terminology; do not expose internal identifiers as labels or rename identifiers merely to improve the UI. Match the label to the actual scope of the action. Internal-only template parameters do not require UI labels.
- Put non-secret deployment configuration in one directory, for example `deploy/variables/variables.shared.yml` and `variables.<env>.yml`. Include resource names, not just settings that vary today. Define shared values once and environment overrides explicitly. Keep secrets in the existing secret store, with references rather than secret values in YAML.
- Bicep and reusable deployment components consume configuration. Keep naming expressions in central variable templates loaded at the consuming stage or job scope. Do not define a parallel environment configuration or a naming-policy function in Bicep, JSON parameter files, pipeline stages or workflow jobs. Typed input contracts remain useful; they do not own configuration values. Generated parameter files are acceptable adapters when they are derived from the authoritative YAML rather than maintained separately.
- Reuse deployment behavior. Pipeline templates, reusable workflows and scripts are implementation boundaries. For repo-local Azure Pipelines templates, prefer reading the stage/job variable context directly rather than declaring and forwarding every configuration value as a template parameter. This creates a shared variable contract, so use consistent names and document required variables. Reserve template parameters for run choices, structural expansion inputs such as the environment identifier, or independent reusable contracts where explicit inputs are justified. A template parameter is not automatically an operator run choice.
- Preserve the distinction between configuration and execution results. Build IDs, selected artifact versions and deployment outputs are run data. Consume actual outputs where appropriate rather than trying to maintain them in static YAML. Do not replace platform-required identifiers or resource references with redundant configurable knobs.
- For Azure Pipelines, define the environment list once as a static variable and use `split` plus `each` to expand a shared stage definition. Load the appropriate variable template inside each stage. Keep run choices in entry-point parameters. Keep promotion dependencies and approval environments explicit in the generated stages.
- For GitHub Actions, preserve the same ownership and reuse convention using repo-owned configuration and reusable deployment tooling. Do not prescribe Azure variable-template syntax or an `each` equivalent. Use a matrix for independent deployments when appropriate; use explicit jobs calling reusable deployment logic when the promotion graph is clearer that way. Repeating small orchestration declarations is preferable to obscuring dependencies or duplicating deployment steps.

## Good example

Azure Pipelines entry point, showing environment expansion rather than a complete deployment pipeline:

```yaml
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
```

The shared configuration file includes the compile-time environment list:

```yaml
variables:
  - name: environments
    value: dev,tst,prd
  - name: location
    value: westeurope
```

File `deploy/variables/variables.dev.yml` owns DEV-specific configuration:

```yaml
variables:
  - name: subscription
    value: orders-development
  - name: subscriptionId
    value: 00000000-0000-0000-0000-000000000000
  - name: deploymentEnvironment
    value: orders-dev
  - name: hubAddressPrefix
    value: 10.20.0.0/22
  - name: appServiceSku
    value: B1
  - name: deployStagingSlot
    value: 'false'
```

File `deploy/variables/variables.names.yml` owns resource naming expressions. It is expanded inside each stage, with the loop's environment identifier passed explicitly. The variable file does not implicitly capture the caller's loop variable.

```yaml
parameters:
  - name: environment
    type: string

variables:
  - name: resourceGroupName
    value: orders-${{ parameters.environment }}-we-rg
  - name: vnetName
    value: orders-${{ parameters.environment }}-we-vnet
```

This keeps names scoped per stage without defining naming policy in the main pipeline. Exceptional names can instead be explicit values in `variables.<env>.yml`. Define a name in one file only; do not depend on conflicting declarations or implicit override order. A naming template's environment parameter is expansion plumbing, not a queue-time configuration object.

File `deploy/deploy.jobs.yml` consumes the stage variables directly. It documents its configuration contract without duplicating it as parameters:

```yaml
# Requires subscription, subscriptionId, location, deploymentEnvironment,
# resourceGroupName and vnetName in the stage variable context.
parameters:
  - name: forceFullDeployment
    type: boolean
    default: false

jobs:
  - deployment: Deploy
    environment: ${{ variables.deploymentEnvironment }}
    pool:
      vmImage: ubuntu-latest
    strategy:
      runOnce:
        deploy:
          steps:
            - checkout: self
            - task: AzureCLI@2
              inputs:
                azureSubscription: ${{ variables.subscription }}
                scriptType: bash
                scriptLocation: scriptPath
                scriptPath: deploy/deploy.sh
                arguments: >-
                  --subscription-id "$(subscriptionId)"
                  --location "$(location)"
                  --resource-group-name "$(resourceGroupName)"
                  --vnet-name "$(vnetName)"
                  --force-full-deployment ${{ parameters.forceFullDeployment }}
```

The script is an illustrative deployment boundary, not an existing implementation. It must accept and validate these arguments and pass the relevant values to Bicep. Script arguments and Bicep parameters remain explicit process/module interfaces; the eliminated boilerplate is forwarding the same configuration through every YAML template layer. `variables.tst.yml` and [variables.prd.yml](../../../harness/examples/fixtures/e-006/variables/variables.prd.yml) supply the corresponding environment settings using the same keys.

These snippets illustrate ownership and expansion only. A production implementation must preserve the intended dependency graph, approval gates and configuration-to-IaC mapping. Variables are strings in Azure Pipelines; convert explicitly when passing booleans, numbers or structured values into typed contracts. Values needed for stage expansion must exist at template expansion time, not be produced by an earlier job.

## Bad example

```yaml
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
```

This exposes stable environment configuration as run inputs. Moving some values to YAML while deriving the rest in a Bicep naming function still divides configuration ownership.

# Further lessons inferred for review

These follow from the examples but are not additional owner-approved rules:

- Separate orchestration, configuration and deployment implementation. YAML centralization alone does not improve a pipeline that still embeds substantial PowerShell or deployment logic. IAC.8 already covers scripts outside pipelines.
- Keep configuration adapters narrow. A loader may validate required keys, types and environment completeness, but should not become a new deployment framework or a second naming engine.
- Distinguish environment defaults from intentional run overrides. A setting such as staging-slot deployment belongs in environment configuration unless the operator actually needs to choose it per run. Being a boolean does not make a value a run parameter.
- Reuse the built artifact across environments. Environment expansion should vary configuration and promotion controls, not rebuild application binaries for each target.

# Validator experiment, 2026-11-01

Tested with the owner-requested `azure-pipeline-validator==0.2.1` using `--lint --schema`, against an isolated fixture with the shared environment list, DEV/TST/PRD variable files, a parameterized names template, and a nested job template reading stage variables. The job contains compile-time and macro variable references, plus assertions for the expected per-environment names; no pipeline was executed.

All 11 YAML files, including four control cases, passed lint. Schema validation rejected the full pipeline, a static-stage equivalent, a minimal `each` example, and a minimal boolean parameter with `default: false`. A plain step pipeline passed. Inspecting nested schema errors identified rejection of the `each` key and boolean defaults. These failures do not establish that Azure's compiler rejects the proposed convention.

Inspecting the installed package also showed that it wraps variable files as step-template references before schema validation. Its schema pass for the naming file therefore does not validate the naming file's contents or its expansion. The tool supplies `yamlOverride` to Azure's preview endpoint but does not upload or inline local included templates; those must exist in the target pipeline repository/ref.

A live preview was not possible: the configured Azure DevOps organization had no usable CLI login, no project or pipeline was selected, and no preview credentials were present in the relevant environment variables. The experiment does not confirm nested variable visibility or final resource names. Finish with a preview against an authenticated existing pipeline whose repository/ref contains the fixture templates, then inspect `finalYaml` for distinct DEV/TST/PRD values. The fixture and captured CLI log were left in `/private/tmp/azure-variable-template-test/` for this session; they are temporary artifacts, not durable verification evidence.

# Not verified

Microsoft explicitly documents parameterized variable templates, including a stage-scoped include, in [Variable templates with parameters](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/templates?view=azure-devops#variable-templates-with-parameters). This confirms the naming-template syntax is supported; it does not establish that the full nested example has been previewed.

The source examples were supplied in conversation; no source repository or live pipeline was inspected. The illustrative snippets have not been compiled by Azure DevOps or executed. No GitHub Actions implementation is proposed here. The exact central directory and configuration adapter remain repository choices. Stage-scoped naming-template expansion and variable visibility in the nested job template still need verification with an Azure DevOps preview run; a local YAML parser cannot establish compiler behavior. IAC.7 and verified E-006 remain authoritative until a reviewed change adopts this proposal.

Azure expression timing and `split` are documented in [Azure Pipelines expressions](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/expressions?view=azure-devops), and variable semantics in [Define variables](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops). GitHub's alternatives are documented in [Reusing workflow configurations](https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations) and [Using jobs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-jobs).

# Processed examples

Prepared as new, unverified examples on 2026-11-01:

- [E-044](../../../harness/examples/e-044-pipeline-inputs-are-run-choices.md)
- [E-045](../../../harness/examples/e-045-pipeline-run-choices-have-display-names.md)
- [E-047](../../../harness/examples/e-047-github-promotion-reuses-deployment-logic.md)
- [E-049](../../../harness/examples/e-049-nested-job-templates-consume-runtime-variables.md)

# Manual Azure pipeline evidence

The owner ran the temporary pipeline. Stage expansion succeeded, but the first nested job check received an empty compile-time expectedEnvironment value. The revised assertions use runtime macros and report unavailable compile-time values separately. The owner confirmed the corrected pipeline worked on 2026-11-01. This establishes runtime access, not nested compile-time visibility, and supersedes the earlier unverified proposal. E-044 and E-049 reflect the observed behavior.
