---
type: Example
title: "E-013 A pipeline step calls a script; it does not contain one"
description: Call standalone parameterized script files from pipeline steps instead of embedding large inline shell or PowerShell blocks.
example_id: E-013
rule: /rules/iac/iac-8-pipelines-call-scripts.md
verdict: violation
status: stable
verified: { by: human:teamvaluegroup, at: 2026-10-27T20:07:13Z }
tags: [pipelines, scripts]
example_file: pipelines/deploy.yml
eval_context_files: [scripts/Register-Deployment.ps1]
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-10-18T21:00:00Z }
sources:
  - id: evidence
    resource: pull request review threads on inline scripts, build agent choice and pipeline triggers (mined 2026-10-18)
---

# Situation

A deployment pipeline runs complex health-checking and registration logic inside an inline YAML script step.

# Why (verdict)

Large inline scripts cannot be linted, tested, or run locally without copy-pasting code out of CI pipelines. Moving logic into a parameterized script file enables local testing, code reuse, and clean pipeline definitions ([IAC.8](../rules/iac/iac-8-pipelines-call-scripts.md)). Prefer cross-platform Ubuntu agents over Windows agents for routine scripting steps.

# Compliant pattern

## Good example

```yaml
trigger:
  branches:
    include: [main]

pool:
  vmImage: ubuntu-latest

steps:
  - task: AzureCLI@2
    displayName: Wait for deployment and register
    inputs:
      azureSubscription: $(serviceConnection)
      scriptType: pscore
      scriptLocation: scriptPath
      scriptPath: $(Build.SourcesDirectory)/scripts/Register-Deployment.ps1
      arguments: -ResourceGroup $(resourceGroupName) -Name $(deploymentName) -TimeoutMinutes 15
```

## Bad example

```yaml
trigger:
  branches:
    include: ['*']

pool:
  vmImage: windows-latest

steps:
  - task: AzureCLI@2
    displayName: Wait for deployment and register
    inputs:
      azureSubscription: $(serviceConnection)
      scriptType: pscore
      scriptLocation: inlineScript
      inlineScript: |
        $deadline = (Get-Date).AddMinutes(15)
        do {
          $state = az deployment group show -g $(resourceGroupName) -n $(deploymentName) --query properties.provisioningState -o tsv
          if ($state -eq 'Succeeded') { break }
          Start-Sleep -Seconds 20
        } while ((Get-Date) -lt $deadline)
        if ($state -ne 'Succeeded') { throw "Deployment is $state" }
        $outputs = az deployment group show -g $(resourceGroupName) -n $(deploymentName) --query properties.outputs | ConvertFrom-Json
        foreach ($o in $outputs.PSObject.Properties) {
          az keyvault secret set --vault-name $(keyVaultName) --name $o.Name --value $o.Value.value | Out-Null
        }
```

# Not verified

Written for this example in neutral names.
