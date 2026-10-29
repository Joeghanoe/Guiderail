#!/usr/bin/env bash
# Read-only access to dependency and runtime state for agents (rules DEL.2, CLD.2). Refuses everything that
# changes a manifest, a lockfile, the restore state or the machine, and keeps advisory lookups opt-in.
#
# Tool contract (Vegviser AI Tool Boundary)
#   Classification:  Read. No manifest, lockfile, package cache or install is changed.
#   Owner:           team:teamvalue-aicoe. Version: the harness commit in .harness/VERSION.
#   Caller identity: the user's own OS account and their own NuGet.config / .npmrc, set up by the user.
#                    There is no read-only identity for a package manager, so there is no layer 1 here: this
#                    allowlist (layer 2) is the whole boundary. Credentials are never accepted as arguments
#                    (--source, --registry and --config are refused); the feeds come from the repo's config.
#   Inputs:          [--allow-network] <dotnet|npm|pnpm> <args>. Allowed, and nothing else:
#                      dotnet --list-sdks | --list-runtimes | --info | --version
#                      dotnet list [project] package [--outdated|--deprecated|--vulnerable] [--format json] ...
#                      dotnet package list ... (the same, new spelling)
#                      npm|pnpm outdated | ls | list | audit, with read options only.
#                    Options that take a value are written --option=value for npm and pnpm.
#   Results:         the CLI's output and exit code (npm outdated exits 1 when something is outdated);
#                    exit 3 with a reason when refused; exit 4 when a human has to act first (dotnet restore
#                    not run, no lockfile, CLI not installed). The wrapper never restores or installs.
#   Side effects:    Not hermetic. `dotnet list package` is always run with --no-restore, so it writes nothing,
#                    but it evaluates the repo's MSBuild files, and a hostile Directory.Build.props/.targets
#                    can run code. --outdated, --deprecated and `npm|pnpm outdated` read package metadata from
#                    the feeds and registries the repo is already configured for (the traffic a build makes).
#                    `dotnet list package --vulnerable` and `npm|pnpm audit` also send the dependency
#                    inventory (package names and versions) to the advisory service; they are refused unless
#                    the caller states --allow-network. That flag is a visible, per-call statement, not a
#                    sandbox; if the user has not asked for an advisory check, ask before adding it.
#   Review trigger:  a new package manager, a new read subcommand or option, or an SDK/npm major version.
# Dependency bumps follow CLD.2 like any other change: the agent proposes the command, a human runs it.
#
# Usage:   dep-read.sh [--allow-network] <dotnet|npm|pnpm> <args...>
# Example: dep-read.sh dotnet list package --outdated --format json
#          dep-read.sh dotnet --list-sdks
#          dep-read.sh --allow-network npm audit --json
# The output feeds the currency gate (DEL.2): redirect it to a file, then
#          python3 .harness/tools/deps/check-currency.py --current currency.json --dotnet-outdated outdated.json
set -euo pipefail

refuse() {
  echo "dep-read: refused: $1" >&2
  echo "Agents only read dependency state (CLD.2). Write the command down for a human to run." >&2
  exit 3
}

allow_network=false
while [[ "${1:-}" == --allow-network ]]; do
  allow_network=true
  shift
done

[[ $# -ge 1 ]] || refuse "no CLI given. Usage: dep-read.sh [--allow-network] <dotnet|npm|pnpm> <args...>"
cli="$1"
shift
call="$cli $*"

for arg in "$@"; do
  case "$arg" in
    --interactive | --interactive=*) refuse "--interactive can wait for a login or a prompt; the agent cannot answer it." ;;
  esac
done

need_network() { # need_network <what>
  [[ "$allow_network" == true ]] ||
    refuse "$1 sends the dependency inventory (package names and versions) to the advisory service. If the user asked for an advisory check, repeat the call as: dep-read.sh --allow-network $call"
}

# A value for an option: no leading dash, no shell-ish characters.
safe_value() { [[ "$1" =~ ^[A-Za-z0-9@._/*,~+][A-Za-z0-9@._/*,~+:-]*$ ]]; }

final=()
restore_target=""

case "$cli" in
  dotnet)
    case "${1:-}" in
      --list-sdks | --list-runtimes | --info | --version)
        [[ $# -eq 1 ]] || refuse "dotnet $1 takes no further arguments."
        final=("$@")
        ;;
      list | package)
        project=""
        if [[ "$1" == list ]]; then
          shift
          if [[ "${1:-}" != package && "${1:-}" != -* && -n "${1:-}" ]]; then
            project="$1"
            shift
          fi
          [[ "${1:-}" == package ]] || refuse "dotnet list ${1:-} is not a read of package state; only 'dotnet list [project] package'."
          shift
        else
          shift
          case "${1:-}" in
            list) shift ;;
            add | remove | update | search | push | download) refuse "dotnet package $1 changes the project or the feed." ;;
            *) refuse "dotnet package ${1:-} is not allowed; only 'dotnet package list'." ;;
          esac
        fi
        opts=()
        has_no_restore=false
        vulnerable=false
        while (($#)); do
          case "$1" in
            --outdated | --deprecated | --include-transitive | --include-prerelease | --highest-patch | --highest-minor)
              opts+=("$1")
              ;;
            --vulnerable)
              vulnerable=true
              opts+=("$1")
              ;;
            --no-restore)
              has_no_restore=true
              ;;
            -f | --framework | -v | --verbosity | --format | --output-version | --project | --file)
              [[ $# -ge 2 ]] || refuse "dotnet: $1 needs a value."
              safe_value "$2" || refuse "dotnet: the value '$2' for $1 is not accepted."
              opts+=("$1" "$2")
              shift
              ;;
            -s | --source | --config | --configfile)
              refuse "dotnet: $1 points the lookup at a feed or config that can carry credentials; the repo's NuGet.config decides."
              ;;
            -*)
              refuse "dotnet list package: option '$1' is not on the read allowlist."
              ;;
            *)
              refuse "dotnet list package: unexpected argument '$1'."
              ;;
          esac
          shift
        done
        [[ "$vulnerable" == false ]] || need_network "'dotnet list package --vulnerable'"
        # Without --no-restore, list package restores first, which writes obj/ and downloads packages.
        if [[ -n "$project" ]]; then
          final=(list "$project" package)
        else
          final=(list package)
        fi
        final+=(${opts[@]+"${opts[@]}"} --no-restore)
        restore_target="$project"
        ;;
      restore | add | remove | update | build | publish | run | test | new | tool | workload | nuget | pack | clean | msbuild | sln | reference | install | format | watch | dev-certs | user-secrets | store | sdk)
        refuse "dotnet $1 changes files, the restore state or the machine. Read with: dotnet list package, dotnet --list-sdks, dotnet --list-runtimes."
        ;;
      *)
        refuse "dotnet ${1:-} is not on the read allowlist (--list-sdks, --list-runtimes, --info, --version, list package, package list)."
        ;;
    esac
    ;;

  npm | pnpm)
    sub=""
    positional=()
    opts=()
    while (($#)); do
      case "$1" in
        --json | -l | --long | -a | --all | -p | --parseable | --prod | --production | -P | --dev | -D | --no-optional | --compatible | -r | --recursive | -g | --global | --workspaces | -ws | --include-workspace-root | --link | --no-color)
          opts+=("$1")
          ;;
        --omit=* | --include=* | --depth=* | --audit-level=* | --prefix=* | --dir=* | --filter=* | --workspace=* | --format=* | --loglevel=*)
          safe_value "${1#*=}" || refuse "$cli: the value in '$1' is not accepted."
          opts+=("$1")
          ;;
        --omit | --include | --depth | --audit-level | --prefix | --dir | -C | --filter | --workspace | -w | --format | --loglevel)
          [[ $# -ge 2 ]] || refuse "$cli: $1 needs a value."
          safe_value "$2" || refuse "$cli: the value '$2' for $1 is not accepted."
          opts+=("$1" "$2")
          shift
          ;;
        --version | -v)
          [[ -z "$sub" && ${#opts[@]} -eq 0 && $# -eq 1 ]] || refuse "$cli $1 only on its own."
          sub="--version"
          ;;
        --fix | --force | -f)
          refuse "$cli: $1 changes the lockfile or node_modules."
          ;;
        --registry | --registry=* | --userconfig* | --globalconfig* | --//* | --otp* | --token* | --auth* | --_auth*)
          refuse "$cli: $1 carries a registry or credential on the command line; the repo's .npmrc decides."
          ;;
        -*)
          refuse "$cli: option '$1' is not on the read allowlist."
          ;;
        *)
          if [[ -z "$sub" ]]; then sub="$1"; else positional+=("$1"); fi
          ;;
      esac
      shift
    done
    case "$sub" in
      --version)
        final=(--version)
        ;;
      outdated | ls | list)
        for p in ${positional[@]+"${positional[@]}"}; do
          [[ "$p" =~ ^@?[a-z0-9][a-z0-9._/-]*$ ]] || refuse "$cli $sub: '$p' is not a package name."
        done
        final=("$sub" ${opts[@]+"${opts[@]}"} ${positional[@]+"${positional[@]}"})
        ;;
      audit)
        ((${#positional[@]} == 0)) || refuse "$cli audit ${positional[0]}: only a plain audit; fixing and signature checks change or fetch more than they report."
        need_network "'$cli audit'"
        final=(audit ${opts[@]+"${opts[@]}"})
        ;;
      install | i | add | ci | remove | rm | uninstall | un | update | up | upgrade | dedupe | prune | rebuild | link | publish | exec | x | dlx | run | run-script | start | test | init | install-test | unlink | pack | version)
        refuse "$cli $sub changes files, installs code or runs scripts. Read with: $cli outdated, $cli ls, $cli audit."
        ;;
      "")
        refuse "no $cli subcommand given (outdated, ls, audit)."
        ;;
      *)
        refuse "$cli $sub is not on the read allowlist (outdated, ls, list, audit)."
        ;;
    esac
    export NPM_CONFIG_UPDATE_NOTIFIER=false NPM_CONFIG_FUND=false
    ;;

  *)
    refuse "unknown CLI '$cli'. Supported: dotnet, npm, pnpm."
    ;;
esac

if ! command -v "$cli" >/dev/null 2>&1; then
  echo "dep-read: $cli is not installed or not on PATH. Ask the user to install it; the agent does not." >&2
  exit 4
fi
export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1

out="$(mktemp)"
err="$(mktemp)"
trap 'rm -f "$out" "$err"' EXIT
rc=0
"$cli" "${final[@]}" </dev/null >"$out" 2>"$err" || rc=$?
cat "$out"
cat "$err" >&2

# Restore is a write (obj/, downloads), so it is the user's to run. Tell the caller what to hand over.
if ((rc != 0)); then
  if [[ "$cli" == dotnet ]] && grep -Eqi "No assets file was found|run restore before|NETSDK1004" "$out" "$err"; then
    echo "dep-read: the project has not been restored, so there is no package data to read." >&2
    echo "Ask the user to run: dotnet restore${restore_target:+ $restore_target}" >&2
    echo "The agent never restores (CLD.2); repeat this command after the user has." >&2
    exit 4
  fi
  if [[ "$cli" != dotnet ]] && grep -Eqi "ENOLOCK|requires an existing lockfile|ERR_PNPM_NO_LOCKFILE" "$out" "$err"; then
    if [[ "$cli" == npm ]]; then fix="npm install --package-lock-only"; else fix="pnpm install --lockfile-only"; fi
    echo "dep-read: there is no lockfile, so $cli cannot read resolved versions." >&2
    echo "Ask the user to run: $fix (and commit the lockfile)." >&2
    echo "The agent never installs (CLD.2); repeat this command after the user has." >&2
    exit 4
  fi
fi
exit "$rc"
