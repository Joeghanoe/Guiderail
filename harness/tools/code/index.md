# C# structural checks

Build: `dotnet build harness/tools/code/CheckTypes.csproj` (SDK 9 or later, with the .NET 9 targeting pack).
The checker uses Roslyn assemblies from the selected SDK, with no NuGet analyzer dependency.

Run from the source tree: `dotnet <absolute-path-to-CheckTypes.dll> Widget.cs Other.cs`.
Add `--baseline <absolute-path-to-baseline-source-tree>` after the paths for change evaluation.
Paths are explicit and relative to the current source tree. The caller supplies the isolated workspace
and baseline; the checker never edits either. Pin the selected SDK and checker commit in run evidence.
Save stdout outside the repository as the JSON report. Exit 0 means no structural findings, 1 means
CODE.5 findings, and 2 means the check could not complete. An error must not be scored as compliance.

Generated files (`.g.cs`, `.generated.cs`, or an auto-generated marker in the first five lines) are
reported not applicable. A partial type may use `Type.Part.cs`. Private nested helpers may remain;
public/internal/protected nested types are findings. Unchanged declarations in the same baseline path
are inherited. A changed declaration in a mixed file is evaluated without requiring unchanged siblings
to move. Audit mode reports all structural violations and does not distinguish inherited issues.

Limitations: this is a syntax check, not a build or semantic analysis. It cannot establish responsibility,
whether a private helper has only one user, or whether a generated marker is truthful. Conditional code
is parsed with default preprocessor symbols; evaluate other configurations separately. Baseline comparison
is textual per declaration; formatting changes may cause a declaration to be considered touched. Other
languages remain covered by review. Run independent build/tests and review alongside this check.

Fixtures: `python -m unittest discover -s tests -p test_code_types.py` after building. The fixed fixture
verdicts exercise the approved scope. They do not change reviewer thresholds or make this a pipeline gate.
