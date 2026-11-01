---
type: Example
title: "E-047 GitHub workflows share a configuration loader and environment deployment"
description: GitHub workflows share a configuration loader and environment deployment.
example_id: E-047
rule: /rules/iac/iac-7-configuration-placement.md
verdict: boundary
status: stable
verified: { by: human:joeghanoe, at: 2026-11-01T19:18:40Z }
tags: [feedback, regression]
generated: { by: codex/unknown, at: 2026-11-01T20:00:00Z }
eval_split_files: true
owner: human:joeghanoe
stale_after: 2027-05-01T00:00:00Z
sources:
  - id: requirement
    resource: owner clarification that configuration ownership and reuse apply across platforms but Azure split/each is not required in GitHub Actions
  - id: workflow-reference
    resource: TeamNOW.Aquarium@8d901ef27ce9d716daf15ceefe49ba25f7397a0f:.github/workflows/{ci,release,load-params,deploy-environment}.yml
  - id: infrastructure-reference
    resource: TeamNOW.Aquarium@8d901ef27ce9d716daf15ceefe49ba25f7397a0f:TeamNOW.Infra/Infra/{main.bicep,parameters/global.json,parameters/dev.json,parameters/prd.json}
---

# Situation

CI and manual release workflows call one environment deployment workflow. Like Azure Pipelines, configuration lives in one `deploy/variables/` directory: `variables.shared.yml` owns shared values and the environment list, and `variables.<env>.yml` owns environment settings and resource names. Each file uses `variables` entries with `name` and `value` fields.

GitHub Actions does not load Azure variable templates. A reusable loader reads the YAML, merges shared and environment entries, and publishes one JSON output. Consumers use `fromJSON(needs.load-params.outputs.params)` rather than forwarding every setting through workflow inputs. Keep workflow inputs for the selected environment, source ref, changed-component flags and deploy-all choice. The workflow must load configuration from the same ref as the deployment content.

This adapts the reference repository's reusable loader/output and environment-deployment architecture to the owner's YAML convention. Its existing loader uses JSON files; that is provenance, not a requirement to keep new configuration in JSON. Resource names stay in the central files. The reference's Bicep naming function is not adopted. Literal names per environment are appropriate here; Azure template expressions inside naming files would need an explicit adapter before GitHub could interpret them. Do not pretend that GitHub evaluates Azure expressions.

Explicit jobs and environment approval boundaries remain valid. Do not require an Azure-style `each` loop or force a matrix to obscure a promotion graph.

## Good example

```text
# File: .github/workflows/ci.yml
on:
  push:
    branches: [main]
jobs:
  deploy-development:
    uses: ./.github/workflows/deploy-environment.yml
    with:
      environment_name: Development
      env_code: dev
      ref: ${{ github.sha }}
# File: .github/workflows/release.yml
on:
  workflow_dispatch:
    inputs:
      version:
        description: Version to deploy
        required: true
        type: string
jobs:
  deploy-production:
    uses: ./.github/workflows/deploy-environment.yml
    with:
      environment_name: Production
      env_code: prd
      ref: ${{ inputs.version }}
      deploy_all: true
# File: .github/workflows/load-params.yml
on:
  workflow_call:
    inputs:
      env:
        required: true
        type: string
      ref:
        required: true
        type: string
    outputs:
      params:
        value: ${{ jobs.load.outputs.params }}
jobs:
  load:
    runs-on: ubuntu-latest
    outputs:
      params: ${{ steps.merge.outputs.params }}
    steps:
      - uses: actions/checkout@v7
        with:
          ref: ${{ inputs.ref }}
      - run: python -m pip install -r .github/scripts/requirements.txt
      - id: merge
        run: python .github/scripts/load-params.py
        env:
          ENV_CODE: ${{ inputs.env }}
# File: .github/scripts/requirements.txt
PyYAML==6.0.3
# File: .github/scripts/load-params.py
import json
import os
from pathlib import Path
import yaml

root = Path('deploy/variables')
def read_variables(path):
    entries = yaml.safe_load(path.read_text())['variables']
    return {entry['name']: entry['value'] for entry in entries}

shared = read_variables(root / 'variables.shared.yml')
environment = os.environ['ENV_CODE']
if environment not in shared['environments'].split(','):
    raise SystemExit('Unknown environment')
params = shared | read_variables(root / f'variables.{environment}.yml')
with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
    output.write('params=' + json.dumps(params, separators=(',', ':')) + '\n')
# File: .github/workflows/deploy-environment.yml
on:
  workflow_call:
    inputs:
      environment_name:
        required: true
        type: string
      env_code:
        required: true
        type: string
      ref:
        required: true
        type: string
      deploy_all:
        required: false
        type: boolean
        default: false
jobs:
  load-params:
    uses: ./.github/workflows/load-params.yml
    with:
      env: ${{ inputs.env_code }}
      ref: ${{ inputs.ref }}
  deploy:
    needs: load-params
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment_name }}
    steps:
      - uses: actions/checkout@v7
        with:
          ref: ${{ inputs.ref }}
      - run: bash deploy/show-config.sh
        env:
          LOCATION: ${{ fromJSON(needs.load-params.outputs.params).location }}
          RESOURCE_GROUP_NAME: ${{ fromJSON(needs.load-params.outputs.params).resourceGroupName }}
# File: deploy/show-config.sh
printf 'Selected deployment target: %s in %s\n' "$RESOURCE_GROUP_NAME" "$LOCATION"
# File: deploy/variables/variables.shared.yml
variables:
  - name: environments
    value: dev,prd
  - name: location
    value: westeurope
# File: deploy/variables/variables.dev.yml
variables:
  - name: resourceGroupName
    value: orders-dev-we-rg
# File: deploy/variables/variables.prd.yml
variables:
  - name: resourceGroupName
    value: orders-prd-we-rg
```

## Bad example

```text
on: workflow_dispatch
jobs:
  dev:
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy/deploy.sh --resource-group orders-dev-we-rg
  prd:
    needs: dev
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy/deploy.sh --resource-group orders-prd-we-rg
```

# Evidence and limits

Inspected the local reference checkout on 2026-11-01 at the revision recorded in sources. The example keeps its loader-output and reusable-workflow architecture, adapts the configuration format to the requested YAML convention, and forwards the selected ref to configuration loading. No customer identifiers or secrets are copied. The last step prints configuration instead of deploying; authentication, artifacts and infrastructure output wiring are outside this focused fixture. Local checks exercise the loader and its environment selection, not a live GitHub deployment.
