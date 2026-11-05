---
type: Example
title: "E-049 Nested job templates consume stage variables at runtime"
description: Nested job templates consume stage variables at runtime.
example_id: E-049
rule: /rules/iac/iac-7-configuration-placement.md
verdict: violation
status: stable
verified: { by: human:teamvaluegroup, at: 2026-11-01T19:18:40Z }
tags: [feedback, regression]
generated: { by: codex/unknown, at: 2026-11-01T20:00:00Z }
eval_split_files: true
---

# Situation

The owner ran the temporary Azure pipeline. Stages expanded, but the first nested job check received an empty compile-time stage variable. Replacing the runtime assertion inputs with macros worked. This case tests that specific nested job-template composition; it does not ban template expressions for root/static variables, stage-local declarations or template parameters. The test must not call an empty compile-time value a successful expansion.

## Good example

```text
# File: azure-pipelines.yml
trigger: none
stages:
  - stage: Deploy_dev
    variables:
      - template: variables/variables.dev.yml
    jobs:
      - template: jobs/check.yml
# File: variables/variables.dev.yml
variables:
  - name: expectedEnvironment
    value: dev
# File: jobs/check.yml
jobs:
  - job: Check
    steps:
      - bash: test "$EXPECTED_ENVIRONMENT" = dev
        env:
          EXPECTED_ENVIRONMENT: $(expectedEnvironment)
```

## Bad example

```text
# File: azure-pipelines.yml
trigger: none
stages:
  - stage: Deploy_dev
    variables:
      - template: variables/variables.dev.yml
    jobs:
      - template: jobs/check.yml
# File: variables/variables.dev.yml
variables:
  - name: expectedEnvironment
    value: dev
# File: jobs/check.yml
jobs:
  - job: Check
    steps:
      - bash: test "$EXPECTED_ENVIRONMENT" = dev
        env:
          EXPECTED_ENVIRONMENT: ${{ variables.expectedEnvironment }}
```

# Evidence and limits

Prepared from the owner's feedback queue on 2026-11-01. Source snippets use neutral names. Model evaluation tests reviewer behavior, not execution of these snippets. The owner approved this example in the processing session on 2026-11-01. Approval concerns the expected reviewer behavior, not execution of the snippet.

# Related guidance

This example illustrates [IAC.7 Per-environment values are configuration; everything fixed is written once in the pipeline](../rules/iac/iac-7-configuration-placement.md). The `rule` metadata records the same relationship for tooling.
