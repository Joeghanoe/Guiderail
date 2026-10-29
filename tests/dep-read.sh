#!/usr/bin/env bash
# Tests for harness/tools/deps (dep-read.sh and check-currency.py). Sourced by tests/run.sh, which provides
# expect, $here, $h, $tmp, $pass and $fail. No network: dotnet, npm and pnpm are stubs on PATH.
# shellcheck shell=bash

echo "== dep-read"
depbin="$tmp/depbin"
mkdir -p "$depbin"
: >"$tmp/depcalls"
for cli in dotnet npm pnpm; do
  cat >"$depbin/$cli" <<'STUB'
#!/usr/bin/env bash
# Records the call, then answers like the real CLI would in the situations under test.
name="$(basename "$0")"
echo "$name $*" >>"$STUB_LOG"
if [[ "${STUB_NORESTORE:-}" == 1 && "$name" == dotnet ]]; then
  echo "No assets file was found for \`/repo/Api/Api.csproj\`. Run restore before running this command."
  exit 1
fi
if [[ "${STUB_NOLOCK:-}" == 1 && "$name" != dotnet ]]; then
  echo "npm ERR! code ENOLOCK" >&2
  echo "ERR_PNPM_NO_LOCKFILE" >&2
  exit 1
fi
if [[ "${STUB_OUTDATED_EXIT:-}" == 1 ]]; then echo "{}"; exit 1; fi
echo "$name $*"
STUB
  chmod +x "$depbin/$cli"
done
dr() { PATH="$depbin:$PATH" STUB_LOG="$tmp/depcalls" "$h/tools/deps/dep-read.sh" "$@"; }
dr_keep() { dr "$@" 2>&1 | tee "$tmp/dr.out"; return "${PIPESTATUS[0]}"; }

# pass-through of the reads
expect 0 "dotnet list package --outdated passes through" dr dotnet list package --outdated
dr_keep dotnet list package --outdated >/dev/null
expect 0 "pass-through reaches dotnet with --no-restore added" grep -qx "dotnet list package --outdated --no-restore" "$tmp/dr.out"
expect 0 "dotnet list package --outdated --format json" dr dotnet list package --outdated --format json
expect 0 "dotnet list package for a named project" dr dotnet list src/Api/Api.csproj package --outdated --include-transitive
expect 0 "dotnet package list (new spelling)" dr dotnet package list --outdated
expect 0 "dotnet list package --deprecated" dr dotnet list package --deprecated
expect 0 "dotnet --list-sdks" dr dotnet --list-sdks
expect 0 "dotnet --list-runtimes" dr dotnet --list-runtimes
expect 0 "npm outdated --json" dr npm outdated --json
expect 0 "npm ls --all" dr npm ls --all
expect 0 "pnpm outdated --format json" dr pnpm outdated --format json
expect 0 "pnpm outdated --filter=./web" dr pnpm outdated --filter=./web
expect 3 "unknown CLI" dr yarn outdated
expect 3 "no CLI" dr
expect 1 "npm outdated exit 1 (something is outdated) is passed through" env STUB_OUTDATED_EXIT=1 PATH="$depbin:$PATH" STUB_LOG="$tmp/depcalls" "$h/tools/deps/dep-read.sh" npm outdated --json

# the network flag is opt-in
expect 3 "dotnet --vulnerable is refused by default" dr dotnet list package --vulnerable
dr dotnet list package --vulnerable >/dev/null 2>"$tmp/dr.err" || true
expect 0 "the refusal names the flag to use" grep -q -- "--allow-network dotnet list package --vulnerable" "$tmp/dr.err"
expect 3 "npm audit is refused by default" dr npm audit
expect 3 "pnpm audit is refused by default" dr pnpm audit --json
expect 0 "dotnet --vulnerable with --allow-network" dr --allow-network dotnet list package --vulnerable
expect 0 "npm audit with --allow-network" dr --allow-network npm audit --json
expect 0 "pnpm audit with --allow-network" dr --allow-network pnpm audit --audit-level=high
expect 3 "--allow-network does not unlock a mutation" dr --allow-network npm audit fix
expect 3 "--allow-network does not unlock npm install" dr --allow-network npm install
expect 3 "--allow-network alone" dr --allow-network

# refusals, by class; the stubs log every call that reaches a CLI, so the log must stay empty
: >"$tmp/depcalls"
expect 3 "dotnet add package" dr dotnet add package Foo
expect 3 "dotnet add reference" dr dotnet add Api.csproj reference Lib.csproj
expect 3 "dotnet remove package" dr dotnet remove package Foo
expect 3 "dotnet package add" dr dotnet package add Foo
expect 3 "dotnet package remove" dr dotnet package remove Foo
expect 3 "dotnet nuget push" dr dotnet nuget push x.nupkg
expect 3 "dotnet restore" dr dotnet restore
expect 3 "dotnet restore --force" dr dotnet restore --force
expect 3 "dotnet build" dr dotnet build
expect 3 "dotnet tool install" dr dotnet tool install -g dotnet-outdated-tool
expect 3 "dotnet list reference is not a package read" dr dotnet list reference
expect 3 "dotnet --list-sdks with trailing arguments" dr dotnet --list-sdks --verbosity
expect 3 "dotnet list package --source (feed credentials)" dr dotnet list package --outdated --source https://u:p@feed.example/v3/index.json
expect 3 "dotnet list package --config" dr dotnet list package --outdated --config nuget.config
expect 3 "dotnet list package --interactive" dr dotnet list package --outdated --interactive
expect 3 "dotnet list package with an unknown option" dr dotnet list package --outdated --frobnicate
expect 3 "dotnet list package with a stray argument" dr dotnet list package rm -rf
expect 3 "dotnet option value that is a flag" dr dotnet list package --framework --outdated
expect 3 "npm install" dr npm install
expect 3 "npm i" dr npm i
expect 3 "npm i with a package" dr npm i left-pad
expect 3 "npm ci" dr npm ci
expect 3 "npm update" dr npm update
expect 3 "npm uninstall" dr npm uninstall react
expect 3 "npm run" dr npm run build
expect 3 "npm exec" dr npm exec -- rm -rf x
expect 3 "npm publish" dr npm publish
expect 3 "npm audit fix" dr --allow-network npm audit fix
expect 3 "npm audit --fix" dr --allow-network npm audit --fix
expect 3 "npm outdated --registry" dr npm outdated --registry=https://evil.example
expect 3 "npm outdated with a registry token" dr npm outdated "--//registry.npmjs.org/:_authToken=abc"
expect 3 "npm outdated --interactive" dr npm outdated --interactive
expect 3 "npm with no subcommand" dr npm
expect 3 "npm outdated with a shell-ish package name" dr npm outdated 'x$(id)'
expect 3 "pnpm install" dr pnpm install
expect 3 "pnpm add" dr pnpm add react
expect 3 "pnpm update" dr pnpm update
expect 3 "pnpm dlx" dr pnpm dlx cowsay
expect 3 "pnpm audit --fix" dr --allow-network pnpm audit --fix
expect 3 "pnpm up --interactive" dr pnpm up --interactive
expect 0 "no refused command reached a CLI" test ! -s "$tmp/depcalls"

# restore needed: the wrapper says what to run and does not run it
: >"$tmp/depcalls"
expect 4 "dotnet without a restore tells the caller to ask for one" env STUB_NORESTORE=1 PATH="$depbin:$PATH" STUB_LOG="$tmp/depcalls" "$h/tools/deps/dep-read.sh" dotnet list package --outdated
env STUB_NORESTORE=1 PATH="$depbin:$PATH" STUB_LOG="$tmp/depcalls" "$h/tools/deps/dep-read.sh" dotnet list src/Api/Api.csproj package --outdated >"$tmp/dr.out" 2>&1 || true
expect 0 "the message names the restore command for the project" grep -q "Ask the user to run: dotnet restore src/Api/Api.csproj" "$tmp/dr.out"
expect 0 "the wrapper never ran restore itself" bash -c "! grep -q '^dotnet restore' '$tmp/depcalls'"
expect 4 "npm without a lockfile asks the user" env STUB_NOLOCK=1 PATH="$depbin:$PATH" STUB_LOG="$tmp/depcalls" "$h/tools/deps/dep-read.sh" --allow-network npm audit
expect 4 "pnpm without a lockfile asks the user" env STUB_NOLOCK=1 PATH="$depbin:$PATH" STUB_LOG="$tmp/depcalls" "$h/tools/deps/dep-read.sh" --allow-network pnpm audit
mkdir -p "$tmp/nodotnet"
for tool in env bash mktemp rm cat grep; do ln -sf "$(command -v $tool)" "$tmp/nodotnet/$tool"; done
nodotnet_path="$tmp/nodotnet"
case "$(uname -s)" in MINGW* | MSYS* | CYGWIN*) nodotnet_path=/usr/bin ;; esac   # copied .exe files lose their DLLs
expect 4 "a CLI that is not installed asks the user" env PATH="$nodotnet_path""$h/tools/deps/dep-read.sh" dotnet --list-sdks

# the guard hook lets the wrapper through the way it lets cloud-read through
expect 0 "hook allows dep-read via ~/.harness" bash_hook "~/.harness/tools/deps/dep-read.sh dotnet list package --outdated"
expect 0 "hook allows dep-read via .harness" bash_hook ".harness/tools/deps/dep-read.sh dotnet --list-sdks"
expect 0 "hook allows dep-read with --allow-network" bash_hook "~/.harness/tools/deps/dep-read.sh --allow-network npm audit --json"
expect 0 "hook allows dep-read with output redirected to a file" bash_hook "~/.harness/tools/deps/dep-read.sh dotnet list package --outdated --format json > outdated.json"
expect 0 "hook allows the currency gate" bash_hook "python3 .harness/tools/deps/check-currency.py --current currency.json --dotnet-outdated outdated.json"

# the currency gate (DEL.2)
gate() { python3 -I "$h/tools/deps/check-currency.py" "$@"; }
gate_keep() { gate "$@" 2>&1 | tee "$tmp/gate.out"; return "${PIPESTATUS[0]}"; }
dcur="$tmp/deps/current.json"
mkdir -p "$tmp/deps"
cat >"$dcur" <<'JSON'
{ "asof": "2026-10-28", "dotnet": 10, "node": 24,
  "packages": { "react": "19.1.0", "react-dom": "19.1.0", "Microsoft.EntityFrameworkCore": "10.0.0" } }
JSON

# a repo that is current, and one at the n-1 boundary
mkdir -p "$tmp/deps/current/src/Api" "$tmp/deps/current/web"
cat >"$tmp/deps/current/global.json" <<'JSON'
{ "sdk": { "version": "10.0.100", "rollForward": "latestFeature" } }
JSON
cat >"$tmp/deps/current/src/Api/Api.csproj" <<'XML'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFrameworks>net10.0;net9.0</TargetFrameworks>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.EntityFrameworkCore" Version="9.0.4" />
    <PackageReference Include="Newtonsoft.Json" Version="9.0.1" />
  </ItemGroup>
</Project>
XML
cat >"$tmp/deps/current/web/package.json" <<'JSON'
{
  "name": "web",
  "engines": { "node": ">=23" },
  "dependencies": { "react": "^18.3.1", "react-dom": "^19.0.0", "left-pad": "1.0.0" }
}
JSON
expect 0 "gate passes a repo at current and n-1" gate --repo "$tmp/deps/current" --current "$dcur" --today 2026-10-28
gate_keep --repo "$tmp/deps/current" --current "$dcur" --today 2026-10-28 >/dev/null
expect 0 "the pass says what it checked" grep -q "0 hit(s) (checked 2 target framework(s), 2 runtime/SDK pin(s), 3 package(s))" "$tmp/gate.out"

# two majors behind: names the package and both versions
mkdir -p "$tmp/deps/stale/src/Api" "$tmp/deps/stale/web"
cat >"$tmp/deps/stale/global.json" <<'JSON'
{ "sdk": { "version": "8.0.404" } }
JSON
cat >"$tmp/deps/stale/src/Api/Api.csproj" <<'XML'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
  </PropertyGroup>
  <ItemGroup>
    <!-- <PackageReference Include="Microsoft.EntityFrameworkCore" Version="5.0.0" /> -->
    <PackageReference Include="Microsoft.EntityFrameworkCore" Version="8.0.2" />
  </ItemGroup>
</Project>
XML
cat >"$tmp/deps/stale/web/package.json" <<'JSON'
{
  "name": "web",
  "engines": { "node": "^20" },
  "dependencies": { "react": "^17.0.2" }
}
JSON
expect 1 "gate fails a repo two majors behind" gate_keep --repo "$tmp/deps/stale" --current "$dcur" --today 2026-10-28
expect 0 "the package finding names the package and both versions" grep -q "Api.csproj:7: DEL.2 package Microsoft.EntityFrameworkCore 8.0.2 is 2 major(s) behind current 10.0.0" "$tmp/gate.out"
expect 0 "the react finding names both versions" grep -q "web/package.json:4: DEL.2 package react 17.0.2 is 2 major(s) behind current 19.1.0" "$tmp/gate.out"
expect 0 "the target framework finding names both" grep -q "Api.csproj:3: DEL.2 target framework net8.0 is 2 release(s) behind current net10.0" "$tmp/gate.out"
expect 0 "the SDK pin finding names both" grep -q "global.json:1: DEL.2 SDK 8.0.404 is 2 release(s) behind current .NET 10" "$tmp/gate.out"
expect 0 "the node engine finding names both" grep -q 'engines.node "\^20" allows Node 20, 4 release(s) behind current Node 24' "$tmp/gate.out"
expect 0 "a commented-out reference is not read" bash -c "! grep -q 'Version 5.0.0\|EntityFrameworkCore 5' '$tmp/gate.out'"
expect 0 "n-1 is allowed and n-2 is not (net9.0 passes, net8.0 failed above)" gate --repo "$tmp/deps/current" --current "$dcur" --today 2026-10-28

# the waiver
printf 'Bump later.\n\ndeps: n/a - EF Core 8 until the partner API moves; upgrade tracked in AB#48213\n' >"$tmp/deps/waiver-ok.txt"
printf 'deps: n/a - EF Core 8 until the partner API moves\n' >"$tmp/deps/waiver-nolink.txt"
printf 'deps: n/a - AB#1\n' >"$tmp/deps/waiver-short.txt"
printf 'deps: n/a - https://dev.azure.com/org/proj/_workitems/edit/48213 EF Core 8 pinned\n' >"$tmp/deps/waiver-url.txt"
printf 'We know the framework is old and will upgrade soon.\n' >"$tmp/deps/waiver-prose.txt"
expect 0 "a stated waiver with a backlog item passes" gate --repo "$tmp/deps/stale" --current "$dcur" --today 2026-10-28 --description "$tmp/deps/waiver-ok.txt"
gate_keep --repo "$tmp/deps/stale" --current "$dcur" --today 2026-10-28 --description "$tmp/deps/waiver-ok.txt" >/dev/null
expect 0 "the waiver is shown, with its reason, after the findings" grep -q "waived by the PR description: EF Core 8 until the partner API moves; upgrade tracked in AB#48213" "$tmp/gate.out"
expect 0 "the findings are still printed when waived" grep -q "DEL.2 package Microsoft.EntityFrameworkCore 8.0.2" "$tmp/gate.out"
expect 0 "a backlog URL is accepted as the link" gate --repo "$tmp/deps/stale" --current "$dcur" --today 2026-10-28 --description "$tmp/deps/waiver-url.txt"
expect 1 "a waiver without the backlog item does not count" gate_keep --repo "$tmp/deps/stale" --current "$dcur" --today 2026-10-28 --description "$tmp/deps/waiver-nolink.txt"
expect 0 "the message says the backlog item is missing" grep -q "waiver needs the backlog item" "$tmp/gate.out"
expect 1 "a waiver under 10 characters does not count" gate --repo "$tmp/deps/stale" --current "$dcur" --today 2026-10-28 --description "$tmp/deps/waiver-short.txt"
expect 1 "prose is never read as a waiver" gate --repo "$tmp/deps/stale" --current "$dcur" --today 2026-10-28 --description "$tmp/deps/waiver-prose.txt"
expect 2 "a --description file that does not exist is a usage error, not a waiver" gate --repo "$tmp/deps/stale" --current "$dcur" --today 2026-10-28 --description "$tmp/deps/none.txt"

# "what is current" comes from the wrapper's output
cat >"$tmp/deps/outdated.txt" <<'TXT'
The following sources were used:
   https://api.nuget.org/v3/index.json

Project `Api` has the following updates to its packages
   [net10.0]:
   Top-level Package                       Requested   Resolved   Latest
   > Microsoft.AspNetCore.OpenApi          [8.0.1, )   8.0.1      10.0.1
   > Newtonsoft.Json                       12.0.1      12.0.1     13.0.3
   > Some.Library                          1.0.0       1.0.0      4.0.0

TXT
cat >"$tmp/deps/outdated.json" <<'JSON'
{ "version": 1, "parameters": "--outdated", "sources": [],
  "projects": [ { "path": "Api.csproj", "frameworks": [ { "framework": "net10.0", "topLevelPackages": [
    { "id": "Microsoft.AspNetCore.OpenApi", "requestedVersion": "[8.0.1, )", "resolvedVersion": "8.0.1", "latestVersion": "10.0.1" } ] } ] } ] }
JSON
printf '{"react": {"current": "17.0.2", "wanted": "17.0.2", "latest": "19.1.0", "dependent": "web"}}\n' >"$tmp/deps/npm-outdated.json"
mkdir -p "$tmp/deps/fromtool"
printf '<Project><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>\n' >"$tmp/deps/fromtool/Api.csproj"
printf '{"dotnet": 10, "asof": "2026-10-28"}\n' >"$tmp/deps/dotnet-only.json"
expect 1 "dotnet --outdated text: a framework package two majors behind fails" gate_keep --repo "$tmp/deps/fromtool" --current "$tmp/deps/dotnet-only.json" --dotnet-outdated "$tmp/deps/outdated.txt" --today 2026-10-28
expect 0 "the wrapper-output finding names both versions" grep -q "Microsoft.AspNetCore.OpenApi 8.0.1 is 2 major(s) behind current 10.0.1" "$tmp/gate.out"
expect 0 "a package outside the framework list is not judged" bash -c "! grep -q 'Some.Library' '$tmp/gate.out'"
expect 1 "--all-packages judges every package" gate_keep --repo "$tmp/deps/fromtool" --current "$tmp/deps/dotnet-only.json" --dotnet-outdated "$tmp/deps/outdated.txt" --all-packages --today 2026-10-28
expect 0 "--all-packages names Some.Library 1.0.0 and 4.0.0" grep -q "Some.Library 1.0.0 is 3 major(s) behind current 4.0.0" "$tmp/gate.out"
expect 1 "dotnet --outdated --format json is read too" gate --repo "$tmp/deps/fromtool" --current "$tmp/deps/dotnet-only.json" --dotnet-outdated "$tmp/deps/outdated.json" --today 2026-10-28
expect 1 "npm outdated --json is read" gate --repo "$tmp/deps/fromtool" --current "$tmp/deps/dotnet-only.json" --npm-outdated "$tmp/deps/npm-outdated.json" --today 2026-10-28
: >"$tmp/deps/empty-outdated.txt"
expect 0 "an empty npm outdated means current" gate --repo "$tmp/deps/current" --current "$dcur" --npm-outdated "$tmp/deps/empty-outdated.txt" --today 2026-10-28

# honesty: unknown is not a pass, a restore error is not data
mkdir -p "$tmp/deps/netfx"
printf '<Project><PropertyGroup><TargetFramework>net48</TargetFramework></PropertyGroup></Project>\n' >"$tmp/deps/netfx/Old.csproj"
expect 1 ".NET Framework 4.8 is older than n-1" gate --repo "$tmp/deps/netfx" --current "$dcur" --today 2026-10-28
expect 2 "a repo that targets .NET with no 'dotnet' in --current is a usage error, not a pass" gate --repo "$tmp/deps/current" --current "$tmp/deps/empty-outdated.txt" --today 2026-10-28
expect 2 "no --current at all with a .NET target is a usage error" gate --repo "$tmp/deps/current" --today 2026-10-28
printf 'No assets file was found for `/repo/Api.csproj`. Run restore before running this command.\n' >"$tmp/deps/restore-error.txt"
expect 2 "dotnet restore error text as --dotnet-outdated is refused" gate --repo "$tmp/deps/current" --current "$dcur" --dotnet-outdated "$tmp/deps/restore-error.txt" --today 2026-10-28
expect 2 "an unreadable --current file" gate --repo "$tmp/deps/current" --current "$tmp/deps/none.json"
expect 2 "a missing repo" gate --repo "$tmp/deps/none" --current "$dcur"
expect 2 "an unknown option" gate --bogus
expect 2 "stale current data with --max-age-days" gate --repo "$tmp/deps/current" --current "$dcur" --today 2027-06-01 --max-age-days 90
mkdir -p "$tmp/deps/unresolved"
printf '<Project><PropertyGroup><TargetFramework>$(Tfm)</TargetFramework></PropertyGroup></Project>\n' >"$tmp/deps/unresolved/A.csproj"
gate_keep --repo "$tmp/deps/unresolved" --current "$dcur" --today 2026-10-28 >/dev/null
expect 0 "an unresolved \$(Tfm) is reported as not judged" grep -q "not resolved; not judged" "$tmp/gate.out"
printf 'src/Api/Api.csproj\nREADME.md\n' >"$tmp/deps/changed.txt"
expect 1 "--changed looks at the manifests the PR touches" gate --repo "$tmp/deps/stale" --current "$dcur" --changed "$tmp/deps/changed.txt" --today 2026-10-28
printf 'README.md\n' >"$tmp/deps/changed-none.txt"
expect 0 "--changed with no manifest in the PR checks nothing" gate --repo "$tmp/deps/stale" --current "$dcur" --changed "$tmp/deps/changed-none.txt" --today 2026-10-28
mkdir -p "$tmp/deps/webonly"
printf '{"name": "web", "dependencies": {"react": "^17.0.2"}}\n' >"$tmp/deps/webonly/package.json"
expect 1 "react two majors behind fails with the default framework list" gate --repo "$tmp/deps/webonly" --current "$dcur" --today 2026-10-28
printf '{"frameworks": ["left-pad"]}\n' >"$tmp/deps/webonly/.harness-currency.json"
expect 0 "a repo-level frameworks list replaces the default" gate --repo "$tmp/deps/webonly" --current "$dcur" --today 2026-10-28
