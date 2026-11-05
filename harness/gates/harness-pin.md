---
type: Gate
title: "Harness pin check"
description: The PR pipeline fails when the harness checkout is not at the commit the repo's pipeline pins.
tool: infra/pipelines/ai-review.yml, parameter harnessCommit (a full commit SHA)
owner: team:teamvalue-aicoe
status: stable
tags: [harness]
---

# Coverage

Which harness version reviewed the PR: the checkout of the harness repository must be at `harnessCommit`. The repo holds no copy of the harness, so there is nothing to drift.

# Blind spots

Local work uses whatever [harness](../index.md) points to ([install.sh](../../install.sh)); a developer on an old checkout reviews against old rules until they pull.

# Complementary checks

`bundle.py check`, `bundle.py privacy-check`, [run.sh](../../tests/run.sh) and the reviewer evals in the harness repo's own CI.

# Failure behaviour

Exit 1; the PR step fails.

# Exception route

None: update `harnessCommit` to the intended harness version.

# Refresh trigger

A new harness release that repos should adopt.
