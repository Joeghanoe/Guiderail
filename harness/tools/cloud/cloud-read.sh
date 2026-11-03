#!/usr/bin/env bash
# Read-only access to cloud CLIs for agents (rule CLD.1). Refuses write verbs and reads that return secrets.
#
# Tool contract (Vegviser AI Tool Boundary)
#   Classification:  Read. No state change, no secrets returned.
#   Owner:           team:teamvalue-aicoe. Version: the harness commit in .harness/VERSION.
#   Caller identity: the CLI's own read-only login, set up by the user (HARNESS_AZURE_CONFIG_DIR,
#                    HARNESS_KUBECONFIG). The agent never logs in or switches accounts.
#                    Without HARNESS_AZURE_CONFIG_DIR, az uses the login the user did themselves; then only
#                    layer 2 limits it.
#   Inputs:          <az|terraform|tofu|kubectl|hcloud> <args>. az: anything except state-changing verbs and
#                    secret-returning reads (E-017). The other CLIs: an allowlist of read verbs.
#   Results:         the CLI's output and exit code; exit 3 with a reason when refused; exit 4 when az is not
#                    logged in (the agent asks the user to run `az login`).
#   Side effects:    none intended. Layer 1 (the identity) is what guarantees it.
#   Review trigger:  a new CLI, a CLI major version, or a new kind of secret-returning read.
# This is layer 2. Layer 1, the real boundary, is the identity: the CLI below must be logged in as a
# read-only principal in its own config directory, never with your personal login.
#
# Usage:   cloud-read.sh <az|terraform|tofu|kubectl|hcloud> <args...>
# Example: cloud-read.sh az resource list --resource-group rg-dev --output table
#
# Setup (once, by a human):
#   export HARNESS_AZURE_CONFIG_DIR="$HOME/.azure-reader"
#   AZURE_CONFIG_DIR="$HOME/.azure-reader" az login     # with the Reader account
#   export HARNESS_KUBECONFIG="$HOME/.kube/reader.config"
set -euo pipefail

refuse() {
  echo "cloud-read: refused: $1" >&2
  echo "Agents only read cloud state (CLD.1). Write the command down for a human." >&2
  exit 3
}

[[ $# -ge 1 ]] || refuse "no CLI given. Usage: cloud-read.sh <az|terraform|tofu|kubectl|hcloud> <args...>"
cli="$1"
shift

# Words before the first option, e.g. "storage account keys list" for az.
positional=()
for arg in "$@"; do
  [[ "$arg" == -* ]] && break
  positional+=("$arg")
done
words="$(printf '%s ' "${positional[@]:-}" | tr '[:upper:]' '[:lower:]')"
last=""
if ((${#positional[@]})); then last="${positional[${#positional[@]}-1]}"; fi

# A federated credential is an issuer/subject pair, not a secret; the plain word "credential" still is refused.
words_checked="${words//federated-credential/federated-identity}"
secretish='(^|[ -])(keys?|secrets?|credentials?|password|passwords|token|tokens|sas|connection-string|connection-strings|certificates?|publishing|publish-profile)([ -]|$)'
if grep -Eq "$secretish" <<<"$words_checked"; then
  refuse "'$cli $words' can return a secret."
fi

case "$cli" in
  az)
    if [[ -n "${HARNESS_AZURE_CONFIG_DIR:-}" ]]; then
      export AZURE_CONFIG_DIR="$HARNESS_AZURE_CONFIG_DIR"
    else
      echo "cloud-read: warning: using personal az login (no HARNESS_AZURE_CONFIG_DIR)" >&2
    fi
    # Allow by default, deny what changes state (E-017). az has hundreds of command groups; listing the read
    # verbs of each (monitor, apim, policy, ...) kept refusing harmless reads. The words are checked wherever
    # they stand in the arguments, so `az --subscription x group delete` cannot slip past. Without a separate
    # reader, az uses the login the user did themselves, so layer 1 does not guarantee read-only: this denylist
    # carries it, and a state-changing verb it does not know is allowed. Not logged in means az fails; the user
    # logs in, the agent never does.
    # Command words are the arguments that are not options and not an option's value: `--resource-group set-rg` names a
    # resource group, it does not run `set`. Flags that take no value are listed so the word after them still counts as a
    # command word (`az group --yes delete`). Any other option swallows the next word; if that word is exactly a
    # state-changing verb it is refused anyway (`--foo delete`), which covers a boolean flag this list does not know.
    az_bool_flags=" --yes -y --all --verbose --debug --only-show-errors --no-wait --help -h --force --recursive --no-prompt "
    az_words=()
    az_values=()
    expect_value=false
    for arg in "$@"; do
      lower="$(tr '[:upper:]' '[:lower:]' <<<"$arg")"
      if [[ "$expect_value" == true && "$arg" != -* ]]; then
        az_values+=("$lower")
        expect_value=false
        continue
      fi
      expect_value=false
      if [[ "$arg" == --*=* ]]; then
        continue
      elif [[ "$arg" == -* ]]; then
        [[ "$az_bool_flags" == *" $arg "* ]] || expect_value=true
      else
        az_words+=("$lower")
      fi
    done
    if ((${#az_words[@]} == 0)); then
      [[ "$*" == "--version" || "$*" == "--help" || "$*" == "-h" ]] || refuse "no az command given."
      exec az "$@"
    fi
    az_path="${az_words[*]}"

    case "${az_words[0]}" in
      login | logout | configure | config | upgrade | extension | interactive | feedback)
        refuse "az ${az_words[0]} changes authentication, configuration or the CLI installation. Pass --subscription <id> (Azure) or --org <url> (Azure DevOps) on each call instead."
        ;;
    esac

    # az devops invoke is permitted for read operations (GET/HEAD/OPTIONS without --in-file).
    is_devops_invoke=false
    if ((${#az_words[@]} >= 2)) && [[ "${az_words[0]}" == "devops" && "${az_words[1]}" == "invoke" ]]; then
      is_devops_invoke=true
      devops_method="get"
      args=("$@")
      for ((i = 0; i < ${#args[@]}; i++)); do
        case "${args[i]}" in
          --http-method) devops_method="$(tr '[:upper:]' '[:lower:]' <<<"${args[i + 1]:-}")" ;;
          --http-method=*) devops_method="$(tr '[:upper:]' '[:lower:]' <<<"${args[i]#*=}")" ;;
          --in-file | --in-file=*) refuse "az devops invoke with --in-file changes state." ;;
        esac
      done
      case "$devops_method" in
        get | head | options) ;;
        *) refuse "az devops invoke only with GET, HEAD or OPTIONS (not '$devops_method')." ;;
      esac
    fi

    # A verb is refused as a word of its own or as the start of a compound (delete-instances, create-for-rbac).
    mutating='create|update|delete|remove|add|set|clear|put|patch|post|replace|upsert|upload|copy|cp|sync|move|rename'
    mutating+='|start|stop|restart|reboot|deallocate|reimage|scale|swap|failover|up|run|queue|trigger|invoke|exec'
    mutating+='|submit|send|publish|deploy|build|commit|reset|regenerate|rotate|enable|disable|assign|unassign'
    mutating+='|grant|revoke|attach|detach|associate|disassociate|register|unregister|lock|unlock|approve|reject'
    mutating+='|cancel|abandon|purge|restore|recover|import|install|uninstall|upgrade|login|logout|ssh|rdp|tunnel'
    mutating+='|connect|migrate|configure'
    for ((w = 0; w < ${#az_words[@]}; w++)); do
      word="${az_words[w]}"
      if [[ "$is_devops_invoke" == true && $w -eq 1 && "$word" == "invoke" ]]; then
        continue
      fi
      if grep -Eq "^($mutating)(-|$)" <<<"$word"; then
        refuse "az $az_path: '$word' changes state."
      fi
    done

    for value in ${az_values[@]+"${az_values[@]}"}; do
      if grep -Eq "^($mutating)$" <<<"$value"; then
        refuse "az $az_path: option value '$value' is a state-changing verb; put the command words before the options."
      fi
    done

    # Reads that return a secret, whatever the command is called (the command-path check above covers the rest).
    if grep -Eqi 'listkeys|listsecrets|listcredentials|listconnectionstrings|listaccountsas|listservicesas|vault\.azure\.net' <<<"$*"; then
      refuse "az $az_path can return a secret."
    fi

    if [[ "${az_words[0]}" == "rest" ]]; then
      method="get"
      args=("$@")
      for ((i = 0; i < ${#args[@]}; i++)); do
        case "${args[i]}" in
          --method | -m) method="$(tr '[:upper:]' '[:lower:]' <<<"${args[i + 1]:-}")" ;;
          --method=*) method="$(tr '[:upper:]' '[:lower:]' <<<"${args[i]#*=}")" ;;
        esac
      done
      [[ "$method" == "get" ]] || refuse "az rest only with --method get."
    fi
    # Assume the user is logged in. When az says otherwise, tell the agent to ask the user (never log in).
    err="$(mktemp)"
    trap 'rm -f "$err"' EXIT
    rc=0
    az "$@" 2>"$err" || rc=$?
    cat "$err" >&2
    if ((rc != 0)) && grep -Eqi "az login|az account set|AADSTS|not logged in|credentials have expired|refresh token has expired" "$err"; then
      echo "cloud-read: az is not logged in (or the login expired). Ask the user to run: ! az login" >&2
      echo "The agent never logs in (CLD.1); retry this command after the user has." >&2
      exit 4
    fi
    exit "$rc"
    ;;
  terraform | tofu)
    # Global options such as -chdir=infra come before the subcommand.
    sub=""
    for arg in "$@"; do
      [[ "$arg" == -* ]] || {
        sub="$arg"
        break
      }
    done
    case "$sub" in
      fmt | validate | version | providers) exec "$cli" "$@" ;;
      init)
        [[ " $* " == *" -backend=false "* ]] || refuse "$cli init only with -backend=false."
        exec "$cli" "$@"
        ;;
      *) refuse "$cli $sub reads or changes real state; only fmt, validate, version, providers and init -backend=false." ;;
    esac
    ;;
  kubectl)
    [[ -n "${HARNESS_KUBECONFIG:-}" ]] || refuse "HARNESS_KUBECONFIG is not set; kubectl would use your personal context."
    export KUBECONFIG="$HARNESS_KUBECONFIG"
    case "${positional[0]:-}" in
      get | describe | logs | top | version | api-resources | explain) exec kubectl "$@" ;;
      *) refuse "kubectl ${positional[0]:-} is not a read verb." ;;
    esac
    ;;
  hcloud)
    # T Cloud KooCLI: hcloud <Service> <Operation> --params. Read operations are named List*/Show*/Get*/...
    op="${positional[1]:-}"
    if ! grep -Eq '(List|Show|Get|Describe|Query|Count)' <<<"$op" ||
      grep -Eq '(Create|Update|Delete|Put|Post|Batch|Start|Stop|Reboot|Attach|Detach|Set|Add|Remove|Associate|Resize|Change|Enable|Disable|Encrypt|Decrypt|Sign)' <<<"$op"; then
      refuse "hcloud ${positional[0]:-} $op is not a read operation."
    fi
    exec hcloud "$@"
    ;;
  *) refuse "unknown CLI '$cli'. Supported: az, terraform, tofu, kubectl, hcloud." ;;
esac
