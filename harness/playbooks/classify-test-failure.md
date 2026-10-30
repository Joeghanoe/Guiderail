---
type: Playbook
title: Classify a test failure
description: Sort a failing test into product, test, environment or flaky before anyone changes code.
tags: [testing, defects]
status: stable
---

# Steps

1. Read the failure output and the test's own report (run report, screenshots, logs), read-only.
2. Check the repo's known issues (`docs/common-issues/` or similar) for the literal error text.
3. Classify:

| Class | Signal | Next step |
|---|---|---|
| product | The behaviour under test is wrong | Fix with a layer 0/1 test that fails first (T.4) |
| test | The test asserts something that is no longer the intent | Update the scenario, and say which intent changed |
| environment | Credentials, configuration, data or a dependency in that environment | Point to or write the known issue; no code change |
| flaky | Passes on rerun without a change | An example for the test's rule; fix the timing or isolation, never add a retry only |

4. Report the class, the evidence and the next step. A class that keeps coming back for the same cause is an
   automation candidate (H.2).
