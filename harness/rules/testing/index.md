# Rules

* [T.1 Done means verified, with the same command locally and in CI](t-1-done-means-verified.md) - One verify command runs format, analyzers, build and tests; work is done only when it passes or every skipped step is named.
* [T.2 Services do not create their own I/O](t-2-services-do-not-create-io.md) - HttpClient, configuration, clock and file system come in through dependency injection, so a service can be tested without a network.
* [T.3 Every test runs in its layer, and every layer's gate is in the pipeline](t-3-tests-run-in-their-layer.md) - Local and PR tests need no cloud; DEV tests use test tenants and generated data; a gate that a document promises exists in the pipeline.
* [T.4 A defect found in DEV or production gets a test in layer 0 or 1](t-4-escaped-defects-get-a-test.md) - Every bug that a later layer finds is reproduced by a local or PR test in the fix.
* [T.5 Behaviour the integration suite can reach comes with a scenario](t-5-behaviour-has-a-scenario.md) - If a repo has integration or E2E tests, a change in behaviour adds or updates a scenario that states that intent.
