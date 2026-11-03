---
type: Rule
title: "T.3 Every test runs in its layer, and every layer's gate is in the pipeline"
description: Local and PR tests need no cloud; DEV tests use test tenants and generated data; a gate that a document promises exists in the pipeline.
rule_id: T.3
principle: [/principles/p-06-automation-by-default.md, /principles/p-08-observable-by-design.md]
tags: [testing, integration, e2e, ci]
applies_to: ["**/*Tests*/**", "**/tests/**", "**/cypress/**", "**/*.feature", "**/*.yml", "**/*.yaml"]
enforced_by: [review]
severity: major
status: stable
---

# Rule

| Layer | Where | What runs | Who runs it |
| --- | --- | --- | --- |
| 0. Local | Developer or agent | the project verify: unit tests, integration tests against containers (Azurite, MinIO, SQL) | Developer, agent (Stop hook) |
| 1. PR | CI, no cloud | The same verify command, plus image build, IaC validate, AI review | Pipeline |
| 2. DEV | After deploy to DEV | Smoke, integration and E2E against real services with test tenants and generated data | Pipeline identity, not the agent (CLD.1) |
| 3. PRD | Production | Run reports, alerts, periodic restore or synthetic checks | Platform |

- Layer 0 and 1 tests never reach a cloud service. A test that needs one belongs in layer 2.
- Layer 2 tests only use test tenants and generated data, create their own data per scenario and can run again without manual clean-up.
- A gate that an ADR, README or test strategy promises is implemented in the pipeline. A promise that only lives in a document is a finding.
- A failing layer blocks promotion to the next environment.
