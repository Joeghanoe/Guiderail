# Dependency Tools

Read-only view of dependency and runtime state, and the gate that judges it against DEL.2 (runtime and framework
versions are the current stable release or the one before). Dependency bumps follow CLD.2: the agent proposes the
command, a human runs it. Gate: [framework-currency.md](../../gates/framework-currency.md).

## Routing table

| When the user says | Tool | Command |
|---|---|---|
| "what is outdated?" / "are we on the latest?" | Package reader | `tvh deps read --raw -- dotnet list package --outdated --format json > outdated.json` |
| "npm outdated" | Package reader | `tvh deps read --raw -- npm outdated --json > npm-outdated.json` |
| "which SDK / runtime is installed?" | Runtime query | `tvh deps read --raw -- dotnet --list-sdks` (or `--list-runtimes`) |
| "any vulnerable packages?" | Advisory read, needs the flag | `tvh deps read --raw -- --allow-network dotnet list package --vulnerable` or `... --allow-network npm audit --json` |
| "are we at n-1?" (DEL.2) | Currency gate | `tvh deps currency --raw -- --current currency.json --dotnet-outdated outdated.json --npm-outdated npm-outdated.json --description pr.txt` |

## What the wrapper does and refuses

`dep-read.sh` fronts `dotnet`, `npm` and `pnpm` and allows only reads: `dotnet list package` (also `dotnet package
list`) with `--outdated`, `--deprecated`, `--vulnerable`, `--include-transitive`, `--format json`;
`dotnet --list-sdks`, `--list-runtimes`, `--info`, `--version`; `npm|pnpm outdated`, `ls`, `audit`. Anything else
(`add`, `remove`, `update`, `install`, `ci`, `restore`, `audit fix`, `run`, `--interactive`, `--source`,
`--registry`, a token on the command line) exits 3 with a reason and a line telling the agent to write the command
down for a human. Write `--option=value` for npm and pnpm options that take a value.

- `dotnet list package` is always run with `--no-restore`, so it writes nothing. When the project was not restored
  it exits 4 and names `dotnet restore <project>` for the user to run. npm and pnpm without a lockfile do the same.
- Not hermetic: `--outdated`, `--deprecated` and `npm outdated` read the feeds and registries the repo is already
  configured for. `--vulnerable` and `audit` also send the package inventory to the advisory service, so they need
  `--allow-network` in front of the CLI name. The flag marks the call; it is not a sandbox. Ask the user first when
  they did not ask for an advisory check.
- `dotnet list package` evaluates the repo's MSBuild files; do not point it at a repo you do not trust.
- `npm outdated` exits 1 when something is outdated. The output is still valid JSON.

## The gate

`check-currency.py` takes "current" from files, never the network. `--current` is a JSON file the team maintains,
`{"asof": "2026-10-28", "dotnet": 10, "node": 24, "packages": {"react": "19.1.0"}}`. The `--dotnet-outdated` and
`--npm-outdated` files add the latest version of each package the package manager reports (text or JSON); a package
missing from an outdated listing is current. No `dotnet` in `--current` while the repo targets .NET is exit 2.
Exit 0 pass, 1 findings, 2 usage. See the gate file for what it cannot see.
