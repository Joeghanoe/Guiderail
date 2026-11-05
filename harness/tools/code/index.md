# C# structural checks

Use `tvh code types --raw -- Widget.cs Other.cs` from the source tree for an explicit-file check. The CLI builds the SDK-backed checker in its external evidence directory; no manual DLL path is needed. SDK 10 and its targeting pack must be installed. Add `--baseline <baseline-source-tree>` or `--symbols DEBUG,FEATURE` after the files; use `--symbols none` for an explicitly empty configuration. Source paths remain relative to the working directory.

For repository-scoped change checks and retained verification receipts, use `tvh checks code-types --json -- --repo . --baseline origin/main --symbols none`. The [CLI catalog](../cli/commands.md) records both operations. CLI exit 0 means complete without findings, 1 reports findings, and 2 means incomplete. Native JSON and exit codes remain in retained evidence; `--raw` preserves the native JSON stream for explicit-file callers.

The [checker source](Program.cs) is authoritative for structural mechanics and exclusions.
[test_code_types.py](../../../tests/test_code_types.py) demonstrates the accepted cases. This page documents invocation and
report handling rather than maintaining another list of the policy's exception details.

Limitations: this is a syntax check, not a build or semantic analysis. It cannot establish responsibility,
whether a private helper has only one user, or whether a generated marker is truthful. Conditional code
is parsed with the explicitly selected symbols; callers must enumerate supported configurations. Baseline comparison
is textual per declaration; formatting changes may cause a declaration to be considered touched. Other
languages remain covered by review. Run independent build/tests and review alongside this check.

Fixtures: `python -m unittest discover -s tests -p test_code_types.py` after building. The fixed fixture
verdicts exercise the approved scope. They do not change reviewer thresholds. The [verification runner](../verification/index.md) integrates this checker into the full verify template and an independent reusable PR step.

[run.sh](../../../tests/run.sh) builds the checker and runs its fixtures; CI installs the .NET 10 SDK first.
These fixtures gate checker regressions. Consumer compliance is checked only where the updated verify template or reusable PR pipeline is adopted; see [the gate](../../gates/code-types.md).
JSON schema version 2 adds `inheritedFindings`, `symbols` and `coverage`. Baseline syntax errors
return exit 2. Capture the checker commit and SDK version alongside JSON for reproducibility.

## Project verify

`tvh project verify-config path --raw -- [repo-root]` prints, and `tvh project verify-config init --raw -- [--profile generic|service|web-app] [repo-root]` writes, the project's quick verify command in `~/.golden-path-harness/projects/<repo-id>/verify.sh` (the repo-id comes from the origin URL). It is kept outside the repo: CI is the full gate, this is the agent's fast local subset, run by the Stop hook with `--fast` (T.1). A scripts/verify.sh committed in a repo is not used.
