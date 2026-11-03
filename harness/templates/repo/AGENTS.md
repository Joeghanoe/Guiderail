# <Repo name>

<One paragraph: what this repo does, for whom, and the one question it answers.>

TeamValue's harness applies (`.github/instructions/teamvalue.instructions.md`, `.harness/index.md`) and is not repeated here. This file holds only what is specific to this repo.

## Layout

```text
<folders and what lives where; organize first by responsibility, then by implementation kind or external
system where needed; state what may depend on what; name any intentionally shared folder precisely>
```

## Naming

<The repo's resource naming convention, or "TeamValue default: {workload}[-{component}]-{env}-{region}-{type}" (IAC.6). Name where values live: per-environment values in variables.<env>.yml, names and fixed settings in the pipeline (IAC.7).>

## Current decisions

- <decision>: <why>. ADR: `docs/adr/<n>-<name>.md`

## Pitfalls

- <something that cost time, and what to do instead>

## Follow a change across boundaries

<Per kind of change, every file it touches outside the code itself (CODE.7). Mark each entry **checked**, with the test or gate that fails when a side is missing, or **documented** when nothing checks it yet.>

- A new <source / endpoint / event>: <code path>, its registration, its tests, <runbook page>, <infra role>. **checked**: `<TestClass.Method>` | **documented**
- A new error code: <catalog file> and a row in <runbook page>. **checked**: `<test that reads the page>`
- A new config field: the config record, its validation, every existing config file with an explicit default. **checked**: `<test that parses every config file>`
- A renamed telemetry event or property: <alert and workbook files>. **documented**

## Verifying

CI runs format, analyzers, build and tests. The agent's quick check is the project verify in `~/.golden-path-harness/projects/` (`--fast` skips the integration tests); this repo carries no copy of it. Integration tests need <Docker / a test tenant>. <Layer 2: how the DEV tests run, and who runs them.>

## When to ask

<Decisions in this repo that are the maintainer's: storage layout, permissions, cost, data location.>
