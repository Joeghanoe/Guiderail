# Choose tests that can detect a broken requirement

Use approved behavior or a concrete reproduction as the independent expected result. Select the smallest public boundary that exercises the invariant. Domain decisions fit unit tests; database and protocol behavior need integration or contract tests; deployed wiring needs smoke evidence. Preserve scenario identifiers linking integration-reachable behavior to criteria.

For a defect, demonstrate the test failing for the observed behavior before applying the fix, then rerun it and adjacent relevant coverage. A failure caused solely by missing tooling does not reproduce the defect. If the environment cannot reproduce it, retain that limitation and distinguish diagnostic evidence from a regression test.

Assert outputs, persisted effects and externally observable failure behavior. Avoid reproducing the algorithm inside the assertion or testing internal method order. Include relevant error and boundary cases without generating exhaustive combinations unrelated to the requirement.

Hand off criteria, test boundaries, observed results and gaps. For an unexpected failure, use [failure classification](../../../harness/playbooks/classify-test-failure.md); do not weaken assertions just to make the suite green.
