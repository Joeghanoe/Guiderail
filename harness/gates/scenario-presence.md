---
type: Gate
title: "Scenario presence check (T.5)"
description: check-scenarios.py fails a PR that changes a component without changing its scenarios or stating why not.
tool: harness/tools/testing/check-scenarios.py, configured by the repo's .harness-scenarios.json
owner: team:teamvalue-aicoe
status: stable
tags: [testing, e2e]
---

# Coverage

Components listed in `.harness-scenarios.json`, matched by path globs against the PR's changed files.

# Blind spots

Whether the changed scenario covers the changed behaviour (that is review), components missing from the config, and behaviour changed through configuration outside the component's path.

# Complementary checks

AI review of T.5 fit; the E2E run after deploy.

# Failure behaviour

Exit 1; the PR step fails.

# Exception route

A PR description line `e2e: n/a - <reason>` (at least 10 characters), visible to the reviewer.

# Refresh trigger

A new component or test suite in the repo, or a T.5 change.
