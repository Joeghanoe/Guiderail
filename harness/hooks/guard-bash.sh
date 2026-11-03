#!/usr/bin/env bash
# PreToolUse hook for Bash. Exit 2 blocks the call; stderr goes back to the agent.
# A guardrail, not a sandbox (CLD.1): the real boundary is the read-only identity.
set -euo pipefail

input="$(cat)"
cmd="$(jq -r '.tool_input.command // ""' <<<"$input")"

# What the command DOES, as opposed to text it only carries (see guard-scopes.pl). The shell scope drops heredoc bodies that are file
# content and the quoted arguments of prose flags; heredoc bodies fed to a script interpreter go to the narrow checks below, so
# a script that merely mentions an environment variable or a dotenv path is not blocked, and one that dumps the environment or reads
# a dotenv file is. A guardrail, not a sandbox (CLD.1): the Write tool can create the same file without passing through here.
scopes="$(dirname "${BASH_SOURCE[0]}")/guard-scopes.pl"
raw="$cmd"
cmd="$(perl "$scopes" shell <<<"$raw")"
interp="$(perl "$scopes" interp <<<"$raw")"
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
  grep -Eq '^[[:space:]]*(\./|~/|\$HOME/|"?\$HOME/|/[^[:space:]]*/)?(\.harness|\.golden-path-harness/harness)/tools/cloud/cloud-read\.sh"?[[:space:]]' <<<"$cmd" &&
    ! grep -Eq '[;&|`]|\$\(' <<<"$(unquoted "$cmd")"
}

# SEC.2: never read .env files or dump the environment (.env.example is fine)
stripped="${lc//.env.example/}"
if grep -Eq '(^|[^a-z0-9_])\.env([^a-z0-9_]|$)|\.env\.[a-z]' <<<"$stripped"; then
  block SEC.2 ".env files are never read. Use .env.example for the structure."
fi
# `env` and `set` dump the environment only as a command (start of the line, or after ; & | or a subshell), not as a word in text;
# `env FOO=1 dotnet test` runs a program and is fine. `printenv` is a dump wherever it appears.
if word 'printenv' || grep -Eq '(^|[;&|(`])[[:space:]]*env([[:space:]]+-[a-z0-9-]+)*[[:space:]]*($|[;&|)`])|(^|[;&|(`])[[:space:]]*set[[:space:]]*($|[;&|)`])|/proc/[^[:space:]]*/environ' <<<"$lc"; then
  block SEC.2 "dumping the environment."
fi
if grep -Eq 'os[[:space:]]*\.[[:space:]]*environ|process[[:space:]]*\.[[:space:]]*env|get-childitem[[:space:]]+env:' <<<"$lc"; then
  block SEC.2 "dumping the environment through a scripting language."
fi

# SEC.2 for code that arrives as a heredoc to a script interpreter: judge what it does with the environment and with dotenv files, not which
# words it contains. Reading one named variable (process.env.PORT, os.environ['HOME']) is how programs get configuration and is fine;
# printing or iterating the whole environment, or opening a dotenv file, is not.
if [[ -n "$interp" ]]; then
  ilc="$(tr '[:upper:]' '[:lower:]' <<<"$interp")"
  if grep -Eq '(print|println|pprint|pp|puts|console\.(log|error|info|dir|table)|json\.(dumps|dump|stringify)|write|echo)[[:space:]]*\(?[[:space:]]*(dict\(|list\(|object\.[a-z]+\()?[[:space:]]*(os[[:space:]]*\.[[:space:]]*environ|process[[:space:]]*\.[[:space:]]*env)[[:space:]]*[,)]|os[[:space:]]*\.[[:space:]]*environ[[:space:]]*\.[[:space:]]*(items|keys|values|copy)[[:space:]]*\(|dict\([[:space:]]*os[[:space:]]*\.[[:space:]]*environ|(^|[^a-z_])for[[:space:]]+[a-z_, ]+[[:space:]]+in[[:space:]]+(os[[:space:]]*\.[[:space:]]*environ|process[[:space:]]*\.[[:space:]]*env)|object\.(keys|entries|values)\([[:space:]]*process[[:space:]]*\.[[:space:]]*env[[:space:]]*\)|getenvironmentvariables[[:space:]]*\(|get-childitem[[:space:]]+env:' <<<"$ilc"; then
    block SEC.2 "a script that prints or iterates the whole environment. Read the one variable you need, by name."
  fi
  if grep -Eq '(open|readfile|readfilesync|read_text|read_file|load_dotenv|dotenv_values|file_get_contents)[[:space:]]*\([^)]*\.env([^a-z0-9_]|$)|get-content[[:space:]]+[^[:space:]]*\.env([^a-z0-9_]|$)|(from|import|require)[[:space:](]*.?dotenv|dotenv[./](config|load)' <<<"$ilc"; then
    block SEC.2 "a script that reads a dotenv file. Use .env.example for the structure."
  fi
fi

# A search or print of text that merely mentions a cloud CLI (`grep 'az login' notes.md`, `echo az`) is not a call to it. Segments that
# start with one of these text-only commands are dropped before the CLD.1 checks below, unless they run something themselves
# (command or process substitution). Anything else, including `xargs az`, `env az`, `bash -c "az ..."`, is still judged.
text_only_dropped() {
  perl -e 'local $/; my $c = <STDIN>; my @keep;
    for my $seg (split /(?:&&|\|\||[;&|\n])/, $c) {
      my $s = $seg; $s =~ s/^\s+//;
      next if $s =~ /^(?:grep|egrep|fgrep|rg|echo|printf|cat|head|tail|wc|sort|uniq|diff|ls)\s/ && $s !~ /\$\(|`|<\(/;
      push @keep, $seg; }
    print join(";", @keep);' <<<"$1"
}
lcc="$(text_only_dropped "$lc")"

# CLD.1: logging in or switching accounts is always done by the user
if grep -Eq '(^|[;&|[:space:]])(az|azd)[[:space:]]+(login|logout|account[[:space:]]+(set|clear))|kubectl[[:space:]]+config[[:space:]]+(use-context|set-credentials)|hcloud[[:space:]]+configure|connect-azaccount|gh[[:space:]]+auth[[:space:]]+login' <<<"$lcc"; then
  block CLD.1 "logging in or switching accounts. The user runs this; tell them the command."
fi

# CLD.1: cloud CLIs only through the wrapper, and the wrapper's identity cannot be swapped. The local
# reader's log-directory variable belongs here too: it widens which files dev-read.sh may open (SEC.2),
# and the tool itself cannot tell whether the agent or the user set it.
if grep -Eq '(harness_azure_config_dir|azure_config_dir|harness_kubeconfig|kubeconfig|harness_dev_log_dirs)=' <<<"$lc"; then
  block CLD.1 "changing which cloud identity the CLI uses, or which files the local reader may open."
fi
# A cloud CLI inside a string that a shell then runs (`bash -c 'az group delete -n x'`, `eval "..."`) is a call, not text: the shell
# scope above drops quoted arguments, so judge the raw command here. Any delete reaches the wrapper's refusal or this block.
raw_lc="$(tr '[:upper:]' '[:lower:]' <<<"$raw")"
if grep -Eq '(^|[;&|(`[:space:]])(bash|sh|zsh|dash|ksh)[[:space:]]+(-[a-z]+[[:space:]]+)*-[a-z]*c([[:space:]]|$)|(^|[;&|(`[:space:]])eval[[:space:]]' <<<"$raw_lc" &&
  grep -Eq '(^|[^a-z0-9_.-])(az|azd|terraform|tofu|kubectl|hcloud|helm)[[:space:]]' <<<"$raw_lc"; then
  block CLD.1 "cloud CLI inside a shell string (bash -c, eval). Call .harness/tools/cloud/cloud-read.sh directly; it refuses delete and every other write."
fi
if grep -Eq "(^|[;&|(\`[:space:]])(az|azd|terraform|tofu|kubectl|hcloud|helm)([[:space:]]|$)|(^|[[:space:]])func[[:space:]]+azure" <<<"$lcc"; then
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
if grep -Eq "(>|tee|sed[[:space:]]+-i|perl[[:space:]]+-i|(^|[[:space:]])(mv|cp|rm|chmod|truncate|ln)[[:space:]])[^|;&]*(\.harness|\.golden-path-harness/harness)/" <<<"$lc"; then
  block H.1 "editing the harness. Propose a case in ~/.golden-path-harness/feedback/ instead."
fi

exit 0
