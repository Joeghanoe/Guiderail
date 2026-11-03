# C# structural checks

Build: `dotnet build harness/tools/code/CheckTypes.csproj` (SDK 10, with the .NET 10 targeting pack).
The checker uses Roslyn assemblies from the selected SDK, with no NuGet analyzer dependency.

Run from the source tree: `dotnet <absolute-path-to-CheckTypes.dll> Widget.cs Other.cs`.
Add `--baseline <absolute-path-to-baseline-source-tree>` after the paths for change evaluation.
For conditional code, pass `--symbols DEBUG,FEATURE` or `--symbols none`. Run once per supported
configuration; the JSON records symbols and coverage for that run, not all possible configurations.
Without this option a file containing `#if` returns an error instead of a compliance result.
Paths are explicit and relative to the current source tree. The caller supplies the isolated workspace
and baseline; the checker never edits either. Pin the selected SDK and checker commit in run evidence.
Save stdout outside the repository as the JSON report. Exit 0 means no structural findings, 1 means
CODE.5 findings, and 2 means the check could not complete. An error must not be scored as compliance.

The [checker source](Program.cs) is authoritative for structural mechanics and exclusions.
`tests/test_code_types.py` demonstrates the accepted cases. This page documents invocation and
report handling rather than maintaining another list of the policy's exception details.

Limitations: this is a syntax check, not a build or semantic analysis. It cannot establish responsibility,
whether a private helper has only one user, or whether a generated marker is truthful. Conditional code
is parsed with the explicitly selected symbols; callers must enumerate supported configurations. Baseline comparison
is textual per declaration; formatting changes may cause a declaration to be considered touched. Other
languages remain covered by review. Run independent build/tests and review alongside this check.

Fixtures: `python -m unittest discover -s tests -p test_code_types.py` after building. The fixed fixture
verdicts exercise the approved scope. They do not change reviewer thresholds. The [verification runner](../verification/index.md) integrates this checker into the full verify template and an independent reusable PR step.

`tests/run.sh` builds the checker and runs its fixtures; CI installs the .NET 10 SDK first.
These fixtures gate checker regressions. Consumer compliance is checked only where the updated verify template or reusable PR pipeline is adopted; see [the gate](../../gates/code-types.md).
JSON schema version 2 adds `inheritedFindings`, `symbols` and `coverage`. Baseline syntax errors
return exit 2. Capture the checker commit and SDK version alongside JSON for reproducibility.
