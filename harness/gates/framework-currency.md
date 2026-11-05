---
type: Gate
title: "Framework currency check (DEL.2)"
description: check-currency.py fails a PR whose target frameworks, SDK pin, Node engine or framework packages are two or more releases behind current, unless a backlog item is linked.
tool: harness/tools/deps/check-currency.py, fed by harness/tools/deps/dep-read.sh output and a current-versions file the team maintains
owner: team:teamvalue-aicoe
status: stable
tags: [delivery, dependencies]
---

# Coverage

`*.csproj` (`TargetFramework`, `TargetFrameworks`, `PackageReference`), `Directory.Build.props`, `Directory.Packages.props`, `global.json` (`sdk.version`), and `package.json` (`engines.node`, dependencies), read as written. A release is a major version: with current N, N and N-1 pass, N-2 and older fail. Packages are judged only when they are on the framework list (a default list, or `frameworks` in `.harness-currency.json`; `--all-packages` judges every package). "Current" comes only from files: `--current`, and the output of `dep-read.sh dotnet list package --outdated` and `npm outdated --json`. The script never calls the network.

# Blind spots

Whether the current-versions file is right. It is maintained by a person; if it still says .NET 9 after .NET 10 shipped, the gate passes net8.0. The script prints a note past 120 days and `--max-age-days` makes it exit 2, but nothing refreshes it. Which packages count as a framework: [DEL.2](../rules/delivery/del-2-frameworks-n-minus-1.md) says "runtime and framework versions" and does not list them, so the default list is a judgement, and a repo can shrink its own list in a PR (review the diff of `.harness-currency.json`).

Runtimes pinned outside the files above are not seen: Dockerfile base images, pipeline `UseDotNet` and `setup-node` steps, `.nvmrc`, and Bicep or HCL runtime stacks such as `linuxFxVersion` or `netFrameworkVersion`. Versions that are not literal are skipped with a `note:` (`$(Tfm)`, MSBuild property indirection, `latest`, `*`, workspace or git references), as are `netstandard` targets (a compatibility contract, not a runtime). Transitive packages are not read. For Node, "current stable" could mean the Current or the LTS line; the file decides, and `engines.node` is judged by the lowest major it allows. Prereleases are excluded only if the input excludes them. The waiver is checked for the shape of a backlog link, not for the item existing, and covers every finding in the PR.

# Complementary checks

AI review of [DEL.2](../rules/delivery/del-2-frameworks-n-minus-1.md) (the rule is `enforced_by: review`), for runtimes pinned outside the manifests and for whether a linked backlog item is a real upgrade plan. Out-of-support and vulnerable versions are a different question: `dep-read.sh --allow-network dotnet list package --vulnerable` and `npm audit`.

# Failure behaviour

Exit 1 with `path:line: DEL.2 message` naming the package or framework and both versions; the PR step fails. Exit 2 when the input is unusable (the repo targets .NET but the current-versions file has no `dotnet`, a `dotnet list package` output that is a restore error, a missing file). A gate that cannot judge fails; it does not pass blind.

# Exception route

A PR description line `deps: n/a - <reason of at least 10 characters>` that includes the upgrade item, as a URL or an id such as `AB#1234`. [DEL.2](../rules/delivery/del-2-frameworks-n-minus-1.md) asks for that backlog item to be linked in the PR, so a waiver without one is ignored and the gate says so.

# Refresh trigger

A new .NET or Node major release (update the current-versions file the same week), a new framework family in use, a new place where a runtime version is pinned, or a change to DEL.2.
