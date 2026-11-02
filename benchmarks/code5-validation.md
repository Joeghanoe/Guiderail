# CODE.5 checker hardening validation

Review base: c2f0493. Validation performed on Windows with .NET SDK 10.0.114. The pipeline now installs SDK 10.0.x; the checker and fixture path target net10.0.

## Changes

- Private-protected nested declarations no longer qualify for the private-helper exception.
- Conditional current or baseline sources require explicit --symbols A,B or --symbols none. Results record the selected configuration; callers must run each supported configuration.
- Unchanged violations appear in inheritedFindings without failing the change evaluation. An unchanged, previously compliant sibling is not mislabeled as an inherited defect.
- Invalid baseline syntax returns an error instead of a compliance result.
- E-020 reflects the accepted convention; harness CI runs the checker build and fixtures. This does not install a blocking CODE.5 gate in consumer projects.

## Validation

- .NET 10 build: passed, zero warnings and errors.
- Seven checker test methods: passed, including 14 structural fixtures, conditional configuration, baseline errors, changed declarations and inherited findings.
- Bundle validation, privacy validation and git diff --check: passed.
- Bash syntax check for tests/run.sh: passed. Shellcheck is unavailable locally.
- Broader Python suite: 30 passed, 2 failed. Both failures reproduce on the unchanged review base: test_behavior_cases_replace_hand_written_scenarios expects CODE.5 but receives CODE.3; test_claude_eval_fails_fast_when_cli_is_not_authenticated expects an unresolved Claude executable path.

Full shell suite: 937 passed, 5 failed (reviewer unit-test group, Claude turn-limit assertion, two coverage-impact absolute-path assertions, and a missing-dotnet CLI assertion). The reviewer unit failures reproduce on the review base; the other shell failures have not been baseline-reproduced. The optional openpyxl-dependent check was skipped because that dependency is absent. The shell run began before the .NET 10 change; the checker was subsequently rebuilt and all seven checker test methods rerun successfully on .NET 10. Hosted Azure Pipelines execution has not been performed locally. Deterministic fixture results do not establish behavioral or functional acceptance for an implementation agent; those dimensions remain unassessed.
