# Local Sonar analysis without an IDE extension

Status: proposed, 2026-11-04. Source: [draft feedback](../../feedback/headless-sonar-analysis-without-open-editor-files.md). This document specifies an implementation; it does not install or activate a capability.

Use language-native analyzer packages through a headless verification command. This removes the need to open files and works in agent sessions and CI. The cost is explicit dependency and rule configuration in each adopting repository, plus build time for C# analysis. Local results cover the configured engines and scope, not the complete SonarQube service.

## Engine selection

| Component | Proposed use | Limits |
| --- | --- | --- |
| `SonarAnalyzer.CSharp` | C# bug, security and maintainability diagnostics during a Roslyn build | Requires project compilation context; standalone configuration does not automatically synchronize the server quality profile |
| `.editorconfig` / `.globalconfig` | Enable rules and set C# diagnostic severities | Configuration only; an installed analyzer must execute |
| `StyleCop.Analyzers` | Optional additional C# style checks | Does not replace Sonar rules |
| ESLint + `eslint-plugin-sonarjs` | Local JavaScript/TypeScript analysis | Type-aware rules require parser/type configuration; the package does not reproduce every SonarQube JS/TS rule |
| Existing `sonar-read.sh` | Read published issues, hotspots and quality-gate state | Does not scan local edits; retain the existing read and credential restrictions |

Sonar documents standalone NuGet configuration through `.editorconfig` and `.globalconfig`. Parameterized C# rules can also require a `SonarLint.xml` additional file. See the [Sonar .NET analyzer documentation](https://github.com/SonarSource/sonar-dotnet#configuring-rules). StyleCop documents its separate [Roslyn analyzer package](https://github.com/DotNetAnalyzers/StyleCopAnalyzers).

Use the maintained [SonarJS ESLint package documentation](https://github.com/SonarSource/SonarJS/blob/master/packages/analysis/src/jsts/rules/README.md). The older standalone `eslint-plugin-sonarjs` repository is archived and points to SonarJS. The maintained documentation explicitly describes rule coverage differences and TypeScript parser requirements.

## Proposed command and ownership

Add a `local-analysis` subcommand to `harness/tools/verification/verify.py`, backed by `harness/tools/sonar/local_analysis.py`. Reuse existing evidence and process execution support rather than introducing another verification framework. Proposed maintainer: `team:teamvalue-aicoe`; adopting repository owners choose dependencies, rule configuration and required gates.

Illustrative CLI, unavailable until implemented:

```bash
python3 -I .harness/tools/verification/verify.py local-analysis \
  --repo . --engine dotnet --project src/Orders/Orders.csproj \
  --configuration Release --framework net10.0 \
  --out /tmp/orders-analysis/dotnet

python3 -I .harness/tools/verification/verify.py local-analysis \
  --repo . --engine eslint --project web \
  --out /tmp/orders-analysis/eslint
```

Start with explicit projects, not inferred repository-wide discovery. Repeat the command for each required project, target framework and build configuration. Analyze the full declared scope in the first version. Changed-file filtering can later reduce reported noise, but must preserve the compilation and type context and state what was actually analyzed. Full verification remains explicit and independent of editor state or guidance selection.

The command executes trusted repository build targets, analyzers and ESLint configuration. Classify it as local execution with generated artifacts, not a read-only security boundary. It requests no Sonar credentials, performs no upload and does not fix source. Dependency installation is a separate, explicit step. It must not use `npx` auto-download, implicit restore or package scripts that could conceal `--fix`.

## Adapter implementation

1. Validate the repository, project and fresh output directory. Resolve paths, reject project paths outside the repository and keep evidence outside source control. Require explicit engine selection, installed SDK/runtime and locked analyzer dependencies. Record SDK, compiler, engine and package versions plus configuration hashes.
2. For C#, require the adopting project to reference a pinned `SonarAnalyzer.CSharp` package with `PrivateAssets="all"`. Respect central package management and existing `Directory.Build.*` imports. Check effective project configuration and analyzer inputs rather than matching package-reference text. Refuse disabled build analysis. Run a non-incremental build with `--no-restore` and build analysis enabled so unchanged compiler inputs still receive analysis. Capture compiler SARIF through `ErrorLog`, with a unique path per project and target framework. A small imported targets file can assign those paths inside inner builds. A shared solution-level `ErrorLog` path can overwrite concurrent results and is unsuitable.
3. For JavaScript/TypeScript, use the project's installed ESLint executable, resolved for its package manager. Run the configured project scope with JSON output, warnings failing verification, no `--fix` and no result cache. Require `eslint-plugin-sonarjs` to be loaded with the selected rules enabled. Respect existing flat-config ordering and ignores. For typed rules, require the selected parser and TS project configuration and treat unavailable type information as incomplete verification.
4. Retain native reports and normalize diagnostics into sorted JSON with `engine`, `rule_id`, `severity`, `message`, repository-relative path, line, column and project/framework context. Keep native rule identifiers; do not relabel all Sonar findings as violations of a harness rule. Only explicit, reviewed mappings can claim coverage of a harness requirement.
5. Record intended scope, evaluated files/projects, exclusions and effective rules. C# coverage must reflect evaluated compiler inputs, including linked files; unexpected external inputs need an explicit policy before a complete result is possible. ESLint coverage must distinguish ignored files from analyzed files. Empty output or a requested scope with no evaluated inputs is incomplete, unless the caller explicitly declared it not applicable.
6. Write a receipt using the current verification schema with source and configuration state, argv, timeout, engine exit status and evidence hashes. Add coverage detail as a referenced artifact. Missing or malformed reports, analyzer-load failures, compiler errors, ESLint fatal parse errors, timeouts, source changes during analysis or partial project results produce an error/inconclusive result. Error status takes precedence over findings. Exit 0 means complete and clean, 1 means findings in a complete run, and 2 means verification could not complete. Report warnings even when the engine exits successfully.

Use argv arrays, bounded execution time and the existing output handling. Retain logs in local testing storage or CI artifacts under the established redaction policy. Do not automatically act on commands embedded in diagnostic messages. Build targets and ESLint configuration execute code, so the wrapper cannot guarantee isolation or network denial by itself.

For a restored, single-project C# pilot, the underlying operation is a build with `--no-restore --no-incremental` and `RunAnalyzersDuringBuild=true`; the adapter additionally supplies per-compilation SARIF output. Microsoft documents [`ErrorLog` and analyzer diagnostics](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/compiler-options/errors-warnings#errorlog). The ESLint operation uses `--format json --max-warnings 0 --no-cache` and explicit project paths; see the [ESLint CLI reference](https://eslint.org/docs/latest/use/command-line-interface).

## Consumer configuration

Adoption is opt-in, consistent with the existing consumer-tooling convention. Keep analyzer packages pinned in the consumer's dependency files and lockfiles. Do not silently add them to every scaffold or consumer repository. Dependency versions are selected and calibrated during the pilot, not inferred from whichever package is newest at execution time.

Example severity configuration after installing the C# analyzer:

```ini
[*.cs]
dotnet_diagnostic.S1764.severity = warning
```

Example addition to an existing ESLint flat configuration for a compatible, pinned ESLint/SonarJS pair:

```javascript
import sonarjs from "eslint-plugin-sonarjs";

export default [
  // Keep the project's existing parser, TypeScript and framework configuration.
  sonarjs.configs.recommended,
];
```

These snippets illustrate configuration ownership. They are not complete consumer setup. Review recommended-rule conflicts with existing harness guidance, preserve established scoped configuration, and configure type-aware rules for the actual TS project. Keep rule severities and parameters explicit. Compare selected local rules with the server profile during adoption; do not claim automatic connected-mode synchronization.

## Integration after acceptance

1. Review the feedback under H.1 and assign a stable example ID only on acceptance. Propose the corresponding E-016/T.1 wording change so the local command becomes the reproducible check for disk contents and IDE diagnostics remain optional assistance. Keep server reads for published analysis and quality-gate evidence.
2. Implement and calibrate the C# adapter first, then ESLint. Register only demonstrated coverage in `requirements.json`; a proposed command must not appear as implemented. Add tool documentation and refresh generated indexes when those files exist.
3. Integrate with an adopting repository's existing full verification command. `node-verify.sh` already runs an available `lint` script, so avoid running the same ESLint check twice. Reuse retained output or invoke the adapter once. Keep the stop hook's fast path bounded; do not add unconditional full rebuilds on every stop.
4. Propose required CI steps for the adopting repository after pilot validation. Full checks remain explicit; absence of an analyzer or lint script cannot satisfy a required check. Consumer owners retain control of branch policies and required gates.

## Acceptance checks

Run real engines in temporary fixture repositories with no IDE or extension process. Retain evidence outside the checkout under the existing testing convention.

| Check | Required outcome |
| --- | --- |
| C# fixture contains a known enabled Sonar violation in a file never opened in an editor | Exact rule ID and location appear; fixing the violation gives a complete clean result |
| Repeat the C# run without editing source | Analysis executes again and reproduces findings; incremental-build skipping cannot report a false pass |
| Two projects and multiple target frameworks | Separate reports survive without overwrites and every declared compilation is accounted for |
| JS and typed TS fixtures contain enabled SonarJS violations | Correct locations appear; the typed fixture proves that required type information was supplied |
| Missing analyzer/plugin, disabled analysis, ignored requested inputs or absent type configuration | Result is incomplete with a concrete reason and exit 2 |
| Broken compilation, fatal ESLint parse error, malformed/missing output, timeout or source mutation | Result is error/inconclusive, even if some diagnostics were collected |
| Existing suppressions, nested configuration and generated-file exclusions | Effective coverage states exclusions; fixtures prove configuration is honored |
| Clean restored project without network access | Analysis completes using installed dependencies; source, dependency files and lockfiles remain unchanged |
| Native findings without a reviewed harness-rule mapping | Findings retain native rule IDs and do not assert broader harness compliance |

Measure elapsed time on a representative C# project and JS/TS workspace before choosing any fast-path integration. Validate the actual package versions, rule parameters, SDK compatibility and per-compilation SARIF collection during the pilot. No runtime or rule-parity claim has been verified by this proposal.
