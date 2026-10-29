#!/usr/bin/env bash
# PreToolUse hook for Bash. Exit 2 blocks the call; stderr goes back to the agent.
# A guardrail, not a sandbox (CLD.1): the real boundary is the read-only identity.
set -euo pipefail

input="$(cat)"
cmd="$(jq -r '.tool_input.command // ""' <<<"$input")"
lc="$(tr '[:upper:]' '[:lower:]' <<<"$cmd")"

block() {
  echo "BLOCKED by harness ($1): $2" >&2
  echo "If this is needed, write the command down and ask the user. See .harness/rules/." >&2
  exit 2
}

word() { grep -Eq "(^|[;&|(\`[:space:]])($1)([[:space:]]|$)" <<<"$lc"; }

# Shell operators only count outside quotes: a KQL query passed to `az monitor ... query` contains `|` as data.
# Single quotes hide everything; inside double quotes `$(` and backticks still run, so they stay visible.
unquoted() {
  perl -0pe "s/'[^']*'//g" <<<"$1" | perl -0pe 's/"(?:[^"\\\$`]|\\.)*"//g'
}

via_wrapper() {
  grep -Eq '^[[:space:]]*(\./|~/|\$HOME/|"?\$HOME/|/[^[:space:]]*/)?\.harness/tools/cloud/cloud-read\.sh"?[[:space:]]' <<<"$cmd" &&
    ! grep -Eq '[;&|`]|\$\(' <<<"$(unquoted "$cmd")"
}

# SEC.2: never read .env files or dump the environment (.env.example is fine)
stripped="${lc//.env.example/}"
if grep -Eq '(^|[^a-z0-9_])\.env([^a-z0-9_]|$)|\.env\.[a-z]' <<<"$stripped"; then
  block SEC.2 ".env files are never read. Use .env.example for the structure."
fi
if word 'env|printenv' || grep -Eq '(^|[;&|[:space:]])set[[:space:]]*($|[;&|])|/proc/[^[:space:]]*/environ' <<<"$lc"; then
  block SEC.2 "dumping the environment."
fi
if grep -Eq 'os[[:space:]]*\.[[:space:]]*environ|process[[:space:]]*\.[[:space:]]*env|get-childitem[[:space:]]+env:' <<<"$lc"; then
  block SEC.2 "dumping the environment through a scripting language."
fi

# CLD.1: logging in or switching accounts is always done by the user
if grep -Eq '(^|[;&|[:space:]])(az|azd)[[:space:]]+(login|logout|account[[:space:]]+(set|clear))|kubectl[[:space:]]+config[[:space:]]+(use-context|set-credentials)|hcloud[[:space:]]+configure|connect-azaccount|gh[[:space:]]+auth[[:space:]]+login' <<<"$lc"; then
  block CLD.1 "logging in or switching accounts. The user runs this; tell them the command."
fi

# CLD.1: cloud CLIs only through the wrapper, and the wrapper's identity cannot be swapped. The local
# reader's log-directory variable belongs here too: it widens which files dev-read.sh may open (SEC.2),
# and the tool itself cannot tell whether the agent or the user set it.
if grep -Eq '(harness_azure_config_dir|azure_config_dir|harness_kubeconfig|kubeconfig|harness_dev_log_dirs)=' <<<"$lc"; then
  block CLD.1 "changing which cloud identity the CLI uses, or which files the local reader may open."
fi
if word 'az|azd|terraform|tofu|kubectl|hcloud|helm' || grep -Eq '(^|[[:space:]])func[[:space:]]+azure' <<<"$lc"; then
  if via_wrapper; then
    exit 0
  fi
  if grep -Eq '^[[:space:]]*(terraform|tofu)([[:space:]]+-[^[:space:]]+)*[[:space:]]+(fmt|validate|version)([[:space:]]|$)' <<<"$lc" &&
    ! grep -Eq '[;&|`]|\$\(' <<<"$cmd"; then
    exit 0
  fi
  block CLD.1 "cloud CLI outside .harness/tools/cloud/cloud-read.sh."
fi
if grep -Eq '(^|[^a-z-])(new|set|remove|update|start|stop|restart|invoke|grant|revoke|publish|import)-az' <<<"$lc"; then
  block CLD.1 "Az PowerShell cmdlet that changes state."
fi
if grep -Eq '(curl|wget|invoke-restmethod|invoke-webrequest|irm|iwr|httpie|http)[[:space:]].*(management\.azure\.com|graph\.microsoft\.com|dev\.azure\.com|visualstudio\.com|vault\.azure\.net|\.otc\.t-systems\.com|myhuaweicloud\.com|api\.github\.com)' <<<"$lc"; then
  block CLD.1 "calling a cloud or DevOps API directly. Use .harness/tools/cloud/cloud-read.sh."
fi

# SEC.2: the Sonar token stays in the shell; reads go through the wrapper
if grep -Eq '(curl|wget|invoke-restmethod|invoke-webrequest|irm|iwr|httpie|http)[[:space:]].*(sonarcloud\.io|sonarqube)' <<<"$lc"; then
  block SEC.2 "calling Sonar directly puts the token on the command line. Use .harness/tools/sonar/sonar-read.sh."
fi
if grep -Eq 'sonar_token' <<<"$lc"; then
  block SEC.2 "the Sonar token is never read, set or printed by an agent."
fi

# SEC.2: the ServiceNow credentials stay in the harness env file; reads go through the wrapper
if grep -Eq '(curl|wget|invoke-restmethod|invoke-webrequest|irm|iwr|httpie|http)[[:space:]].*service-now\.com' <<<"$lc"; then
  block SEC.2 "calling ServiceNow directly. Use .harness/tools/servicenow/sn-get.sh (read-only, allowlisted tables)."
fi
if grep -Eq 'sn_password' <<<"$lc"; then
  block SEC.2 "the ServiceNow password is never read, set or printed by an agent."
fi

# CLD.2: irreversible or outward actions are taken by a human
if grep -Eq 'gh[[:space:]]+(pr[[:space:]]+(merge|review)|workflow[[:space:]]+run|release[[:space:]]+create)' <<<"$lc"; then
  block CLD.2 "merge, approve or run a pipeline."
fi

# CLD.2: an agent may push a named feature branch. The default branch, a release branch, a force push,
# a deletion and tags are for a human. The target must be on the command line, so the check does not
# depend on which upstream the current branch tracks.
check_push() { # check_push <arguments after "git push">
  local -a args positional=()
  local a skip=false
  read -ra args <<<"$1"
  for a in ${args[@]+"${args[@]}"}; do # bash 3.2 treats an empty array as unbound under set -u
    if $skip; then
      skip=false
      continue
    fi
    case "$a" in
      -f | --force | --force-with-lease* | --force-if-includes | --mirror | --all | --tags | --follow-tags | -d | --delete | --prune)
        block CLD.2 "force push, deletion, tags or more than one branch ($a). A human does this." ;;
      -o | --push-option | --repo | --receive-pack | --exec) skip=true ;;
      -*) ;;
      *) positional+=("$a") ;;
    esac
  done
  ((${#positional[@]} >= 2)) || block CLD.2 "push without a named branch. Use: git push -u origin <feature-branch>."

  local default ref dst
  default="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || true)"
  default="$(tr '[:upper:]' '[:lower:]' <<<"${default#origin/}")"
  for ref in "${positional[@]:1}"; do
    [[ "$ref" == +* ]] && block CLD.2 "force push ($ref). A human does this."
    [[ "$ref" == :* ]] && block CLD.2 "deleting a remote branch ($ref). A human does this."
    dst="${ref##*:}"
    dst="${dst#refs/heads/}"
    if [[ "$dst" =~ ^(main|master|head|release/.+)$ || "$dst" == refs/tags/* || (-n "$default" && "$dst" == "$default") ]]; then
      block CLD.2 "push to $dst. The default and release branches are pushed by a human; push a feature branch."
    fi
  done
}
while IFS= read -r push; do
  check_push "$(sed -E 's/^git([[:space:]]+-c[[:space:]]+[^[:space:]]+)*[[:space:]]+push//' <<<"$push")"
done < <(grep -oE "git([[:space:]]+-c[[:space:]]+[^[:space:]]+)*[[:space:]]+push([[:space:]][^;&|\`)]*)?" <<<"$lc" || true)
if grep -Eq '(^|[[:space:]])sudo[[:space:]]|rm[[:space:]]+-[a-z]*r[a-z]*f?[[:space:]]+(/|~)([[:space:]]|$)' <<<"$lc"; then
  block CLD.2 "destructive command."
fi

# The harness is changed through cases and the harness repo, never by an agent in a session (H.1)
if grep -Eq "(>|tee|sed[[:space:]]+-i|perl[[:space:]]+-i|(^|[[:space:]])(mv|cp|rm|chmod|truncate|ln)[[:space:]])[^|;&]*\.harness/" <<<"$lc"; then
  block H.1 "editing the harness. Propose a case in ~/.harness-feedback/ instead."
fi

exit 0
