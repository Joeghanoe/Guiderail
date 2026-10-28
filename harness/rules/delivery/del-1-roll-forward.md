---
type: Rule
title: "DEL.1 Roll forward, never roll back"
description: A broken release is fixed by a new release, not by redeploying an older one.
rule_id: DEL.1
principle: /principles/p-06-automation-by-default.md
tags: [delivery]
applies_to: ["**/*.yml", "**/*.yaml"]
enforced_by: [review]
severity: major
status: stable
sources:
  - id: global
    resource: global.instructions.md (AI Hub main b0cc2ae)
---

# Rule

Release a fix as a new deployment. One artifact or image is built once and promoted through the environments
in order; tags are versions or commit SHAs, never `latest`.
