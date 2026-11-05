---
name: test
description: Design or change automated tests for observable behavior, regressions, and contracts. Use when writing tests or choosing test boundaries; business acceptance sheets use acceptance instead.
---

# Test observable behavior

Inputs are approved criteria or an observed defect and the public boundary under test. Read the applicable [testing rules](../../../harness/rules/testing/index.md). Use [test design](TEST-DESIGN.md) for selecting layers, independent assertions and the defect reproduction loop.

Test domain invariants at unit boundaries and I/O contracts with integration tests. Inject I/O, time and configuration. Avoid tests that copy implementation logic, assert private state or merely count mock calls. Apply the existing defect test-first discipline; a low-impact documentation correction does not need invented tests.

When a test fails unexpectedly, use [failure classification](../../../harness/playbooks/classify-test-failure.md) before changing either product or assertion.

```bash
tvh checks test-presence --input-file <changed-paths.txt> --
tvh checks scenarios --input-file <changed-paths.txt> --
```

Run the repository's test command and retain results. Hand back the criterion-to-test mapping, reproduced failure for defects, current results and any untested boundaries. A green suite does not establish business acceptance or deployment approval.
