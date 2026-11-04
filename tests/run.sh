#!/usr/bin/env bash
# Tests for the harness tools and hooks. No network: cloud CLIs are replaced by stubs on PATH.
# Usage: tests/run.sh
set -uo pipefail

# Git Bash copies instead of linking unless asked; the symlink-escape tests need real links (Windows Developer Mode).
case "$(uname -s)" in MINGW* | MSYS* | CYGWIN*) export MSYS=winsymlinks:nativestrict ;; esac

here="$(cd "$(dirname "$0")/.." && pwd)"
h="$here/harness"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
export GOLDEN_PATH_HOME="$tmp/gp-home"
fail=0
pass=0

expect() { # expect <exit code> <description> <command...>
  local want="$1" what="$2"
  shift 2
  "$@" >"$tmp/out" 2>&1
  local got=$?
  if [[ "$got" == "$want" ]]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    echo "FAIL: $what (exit $got, want $want)"
    sed 's/^/    /' "$tmp/out"
  fi
}

# shim <stub>: on Windows a program launched from Python is found by extension, so give a bash stub a .cmd launcher.
shim() {
  case "$(uname -s)" in
    MINGW* | MSYS* | CYGWIN*) printf '@bash "%s" %%*\r\n' "$(cygpath -m "$1")" >"$1.cmd" ;;
  esac
}

bash_hook() { jq -n --arg c "$1" '{tool_input: {command: $c}}' | "$h/hooks/guard-bash.sh"; }
read_hook() { jq -n --arg p "$1" '{tool_name: "Read", tool_input: {file_path: $p}}' | "$h/hooks/guard-read.sh"; }

echo "== framework registry, retrieval and receipts"
expect 0 "verification registry and receipt contracts" python3 -I "$here/tests/test_verification.py"
expect 0 "selector and edit-context regression contracts" python3 -I "$here/tests/test_context.py"
expect 0 "review-input change detection matrix" python3 -I "$here/tests/test_review_changed.py"
expect 0 "RTK rewrites satisfy Codex's permission contract" python3 -I "$here/tests/test_rtk_codex.py"
expect 0 "unified CLI dispatch, restrictions, receipts and installation" python3 -I "$here/tests/test_cli.py"
expect 0 "complete CLI tool catalog and native command boundaries" python3 -I "$here/tests/test_cli_catalog.py"

expect 0 "standard scanner calibration (real tools when configured)" python3 -I "$here/tests/test_standard_checks.py"

echo "== CODE.5 structural checker"
expect 0 "CODE.5 checker builds" dotnet build "$h/tools/code/CheckTypes.csproj" --disable-build-servers -p:UseSharedCompilation=false
expect 0 "CODE.5 fixtures" python3 -m unittest discover -s "$here/tests" -p test_code_types.py
expect 0 "provider-neutral backup grader controls" python3 -I "$here/tests/test_backup_eval.py"
expect 0 "greenfield design checks" python3 -I "$here/tests/test_design_check.py"
gf="$tmp/greenfield"; mkdir -p "$gf"
pv="$h/tools/code/project-verify.sh"
expect 0 "greenfield-init writes the skeletons" bash "$h/tools/greenfield/greenfield-init.sh" --service "$gf"
expect 0 "greenfield-init keeps what exists" bash "$h/tools/greenfield/greenfield-init.sh" --service "$gf"
expect 1 "design gate fails a fresh skeleton" python3 -I "$h/tools/greenfield/design-check.py" "$gf" --profile service
expect 0 "the repo gets no scripts/verify.sh" test ! -e "$gf/scripts/verify.sh"
expect 0 "the project verify names the service profile" grep -q "^DESIGN_PROFILE=service" "$(bash "$pv" path "$gf")"
expect 0 "the project verify lives under GOLDEN_PATH_HOME" test -x "$(bash "$pv" path "$gf")"
expect 0 "project-verify init keeps what exists" bash "$pv" init --profile generic "$gf"
expect 0 "the kept project verify still names the service profile" grep -q "^DESIGN_PROFILE=service" "$(bash "$pv" path "$gf")"
expect 1 "project-verify rejects an unknown profile" bash "$pv" init --profile nope "$gf"
gw="$tmp/greenfield-web"
expect 0 "greenfield-init --web-app writes the skeletons" bash "$h/tools/greenfield/greenfield-init.sh" --web-app "$gw"
expect 0 "the project verify names the web-app profile" grep -q "^DESIGN_PROFILE=web-app" "$(bash "$pv" path "$gw")"
expect 0 "two repos get two project verifies" test "$(bash "$pv" path "$gf")" != "$(bash "$pv" path "$gw")"
# Stop hook: runs the project verify, ignores one committed in the repo
sv="$tmp/stop-repo"; mkdir -p "$sv/scripts"; git -C "$sv" init -q; git -C "$sv" config user.email t@t; git -C "$sv" config user.name t
echo base >"$sv/a.txt"; git -C "$sv" add -A; git -C "$sv" commit -qm base; echo change >>"$sv/a.txt"
stop() { jq -n '{}' | CLAUDE_PROJECT_DIR="$sv" "$h/hooks/stop-verify.sh"; }
printf '#!/usr/bin/env bash\nexit 1\n' >"$sv/scripts/verify.sh"; chmod +x "$sv/scripts/verify.sh"
expect 0 "stop hook ignores a verify.sh committed in the repo" stop
svp="$(bash "$pv" path "$sv")"; mkdir -p "$(dirname "$svp")"; printf '#!/usr/bin/env bash\necho "fast:$*"; test "$HARNESS_REPO_ROOT" = "%s"; exit 1\n' "$sv" >"$svp"; chmod +x "$svp"
expect 2 "stop hook sends the agent back when the project verify fails" stop
printf '#!/usr/bin/env bash\ntest "${1:-}" = --fast\n' >"$svp"
expect 0 "stop hook passes --fast and succeeds" stop
unset GOLDEN_PATH_HOME
expect 1 "design gate fails a fresh web-app skeleton" python3 -I "$h/tools/greenfield/design-check.py" "$gw" --profile web-app
expect 0 "evaluation artifact freeze controls" python3 -I "$here/tests/test_freeze_eval.py"
expect 0 "candidate runner controls (stand-in adapter, no model)" python3 -I "$here/tests/test_run_candidate.py"
expect 0 "brownfield runner controls (stand-in adapter and grader, no model)" python3 -I "$here/tests/test_run_brownfield.py"
expect 0 "run diagnosis controls (evidence only, no model)" python3 -I "$here/tests/test_diagnose_run.py"
expect 0 "harness usage and denied-command report (traces only, no model)" python3 -I "$here/tests/test_harness_usage.py"
expect 0 "T.1 test-presence check and select --brief" python3 -I "$here/tests/test_test_presence.py"
expect 0 "DEL.5 openapi drift check" python3 -I "$here/tests/test_openapi_drift.py"

echo "== node-verify (a stub package manager on PATH)"
nv="$h/tools/code/node-verify.sh"
mkdir -p "$tmp/nv/bin" "$tmp/nv/app" "$tmp/nv/nolock" "$tmp/nv/partial"
cat >"$tmp/nv/bin/bun" <<'STUB'
#!/usr/bin/env bash
echo "bun $*" >>"$NV_LOG"
[[ "${NV_FAIL:-}" == "$*" ]] && exit 1
exit 0
STUB
chmod +x "$tmp/nv/bin/bun"
printf '{"scripts":{"format:check":"x","build":"x","test":"x"}}' >"$tmp/nv/app/package.json"
: >"$tmp/nv/app/bun.lock"
printf '{"scripts":{"test":"x"}}' >"$tmp/nv/partial/package.json"
: >"$tmp/nv/partial/bun.lock"
printf '{"scripts":{"test":"x"}}' >"$tmp/nv/nolock/package.json"
export NV_LOG="$tmp/nv/log"
: >"$NV_LOG"
expect 0 "node-verify installs frozen, then runs the scripts the project has" env PATH="$tmp/nv/bin:$PATH" bash "$nv" "$tmp/nv/app"
expect 0 "node-verify order is install, format:check, build, test" bash -c "[[ \"\$(tr '\n' '|' <'$NV_LOG')\" == 'bun install --frozen-lockfile|bun run format:check|bun run build|bun run test|' ]]"
: >"$NV_LOG"
expect 0 "node-verify names the steps a project does not define" bash -c "PATH='$tmp/nv/bin:$PATH' bash '$nv' '$tmp/nv/partial' 2>&1 | grep -q \"no 'build' script\""
expect 1 "node-verify fails when a step fails" env PATH="$tmp/nv/bin:$PATH" NV_FAIL="run test" bash "$nv" "$tmp/nv/app"
expect 1 "node-verify refuses a project without a lockfile" env PATH="$tmp/nv/bin:$PATH" bash "$nv" "$tmp/nv/nolock"
expect 1 "node-verify refuses a folder without package.json" env PATH="$tmp/nv/bin:$PATH" bash "$nv" "$tmp/nv"
unset NV_LOG
expect 0 "agent adapters (stand-in CLIs, no provider)" python3 -I "$here/tests/test_adapters.py"
expect 0 "overnight evidence: stub, scenario match, verdicts (no model)" python3 -I "$here/tests/test_overnight_evidence.py"
expect 0 "review usage: tokens, cost, time per run; clean-commit check (no model)" python3 -I "$here/tests/test_usage.py"

echo "== select --changed (a greenfield change)"
sc="$tmp/select-changed"; mkdir -p "$sc"; git -C "$sc" init -q -b main; git -C "$sc" config user.email t@t; git -C "$sc" config user.name t
echo base >"$sc/README.md"; git -C "$sc" add -A; git -C "$sc" commit -qm base
sel_changed() { (cd "$sc" && python3 -I "$h/tools/harness/bundle.py" select --brief --changed); }
expect 0 "design-only change selects no CODE rule" test -z "$(sel_changed | grep '^CODE\.' || true)"
mkdir -p "$sc/src"; echo "class A {}" >"$sc/src/A.cs"
expect 0 "an untracked .cs file selects CODE.5 (git diff alone would miss it)" test -n "$(sel_changed | grep '^CODE.5' || true)"
git -C "$sc" checkout -q -b feat; git -C "$sc" add -A; git -C "$sc" commit -qm code
expect 0 "a committed .cs file on a branch selects CODE.5" test -n "$(sel_changed | grep '^CODE.5' || true)"
nobase="$tmp/select-nobase"; mkdir -p "$nobase/src"; git -C "$nobase" init -q -b work; echo "class B {}" >"$nobase/src/B.cs"
expect 0 "a repo with no base selects for every file" bash -c "cd '$nobase' && python3 -I '$h/tools/harness/bundle.py' select --brief --changed | grep -q '^CODE.5'"
expect 2 "--changed outside a git repository fails loudly" bash -c "cd '$tmp' && GIT_CEILING_DIRECTORIES='$tmp' python3 -I '$h/tools/harness/bundle.py' select --changed"

echo "== project verify template (every check runs)"
vt="$tmp/verify-template"; mkdir -p "$vt/bin" "$vt/repo"; git -C "$vt/repo" init -q -b main
ln -s "$h" "$vt/repo/.harness"
for c in dotnet; do printf '#!/usr/bin/env bash\necho "dotnet $*" >>"%s/calls"\n' "$vt" >"$vt/bin/$c"; chmod +x "$vt/bin/$c"; done
: >"$vt/repo/App.slnx"
GOLDEN_PATH_HOME="$tmp/gp-home" bash "$pv" init --profile service "$vt/repo" >/dev/null
vfy="$(GOLDEN_PATH_HOME="$tmp/gp-home" bash "$pv" path "$vt/repo")"
expect 1 "a failing design gate still fails the project verify" bash -c "cd '$vt/repo' && PATH='$vt/bin:'\$PATH HARNESS_CODE5_EXTERNAL=1 '$vfy' --fast"
expect 0 "a failing design gate does not skip the later build" grep -q "dotnet build" "$vt/calls"
mkdir -p "$vt/repo/src"; echo "public class A {} public class B {}" >"$vt/repo/src/A.cs"
expect 0 "CODE.5 reports two types in one file in --fast although the design gate failed" bash -c "cd '$vt/repo' && PATH='$vt/bin:'\$PATH '$vfy' --fast 2>&1 | grep -q 'CODE.5.file-layout'"

echo "== guard-bash"
expect 0 "dotnet test is allowed" bash_hook "dotnet test Bizure.Backup.slnx -c Release"
expect 0 "git status is allowed" bash_hook "git status"
expect 0 "func start is allowed" bash_hook "func start --port 7071"
expect 0 "terraform fmt is allowed" bash_hook "terraform -chdir=infra fmt -check"
expect 0 "cloud-read wrapper is allowed" bash_hook ".harness/tools/cloud/cloud-read.sh az resource list -g rg-dev"
expect 0 "global cloud-read wrapper is allowed" bash_hook "~/.golden-path-harness/harness/tools/cloud/cloud-read.sh az resource list -g rg-dev"
expect 2 "az login is for the user" bash_hook "az login --tenant x"
expect 2 "az account set is for the user" bash_hook "~/.golden-path-harness/harness/tools/cloud/cloud-read.sh az account set -s x"
expect 2 "Connect-AzAccount is for the user" bash_hook "pwsh -c Connect-AzAccount"
expect 0 ".env.example can be read" bash_hook "cat .env.example"
expect 0 "grep that only mentions az is not a call" bash_hook "grep -rn 'az login' docs"
expect 0 "echo that only mentions az is not a call" bash_hook "echo az group delete"
expect 2 "command substitution inside grep still runs az" bash_hook 'grep x $(az group delete -n a)'
expect 2 "az group delete inside bash -c" bash_hook "bash -c 'az group delete -n rg-dev --yes'"
expect 2 "az group delete inside eval" bash_hook 'eval "az group delete -n rg-dev"'
expect 2 "az delete through sh -lc" bash_hook "sh -lc 'az vm delete -n vm -g rg'"
expect 2 "any delete through the wrapper" bash_hook "~/.golden-path-harness/harness/tools/cloud/cloud-read.sh az group delete -n rg-dev"
expect 0 "bash -c without a cloud CLI" bash_hook "bash -c 'dotnet test'"
expect 2 "xargs az is still a call" bash_hook "echo rg | xargs az group delete"
expect 2 "az after a grep segment" bash_hook "grep x f; az group delete -n rg"
expect 2 "az outside the wrapper" bash_hook "az group delete -n rg-dev --yes"
expect 2 "az chained after the wrapper" bash_hook ".harness/tools/cloud/cloud-read.sh az group list; az group delete -n x"
expect 0 "KQL pipe inside double quotes is data" bash_hook '~/.golden-path-harness/harness/tools/cloud/cloud-read.sh az monitor app-insights query --app x --analytics-query "exceptions | where timestamp > ago(10m) | take 5"'
expect 0 "KQL pipe inside single quotes is data" bash_hook "~/.golden-path-harness/harness/tools/cloud/cloud-read.sh az monitor log-analytics query -w ws -a 'AzureDiagnostics | take 1'"
expect 0 "multi-line KQL inside quotes" bash_hook $'~/.golden-path-harness/harness/tools/cloud/cloud-read.sh az monitor app-insights query --app x --analytics-query "requests\n| where success == false\n| take 5"'
expect 2 "chain after a quoted KQL query" bash_hook '~/.golden-path-harness/harness/tools/cloud/cloud-read.sh az monitor app-insights query --app x --analytics-query "requests | take 1"; az group delete -n x'
expect 2 "pipe outside quotes after the wrapper" bash_hook '~/.golden-path-harness/harness/tools/cloud/cloud-read.sh az group list | sh'
expect 2 "command substitution inside double quotes" bash_hook '~/.golden-path-harness/harness/tools/cloud/cloud-read.sh az monitor app-insights query --app x --analytics-query "$(az group delete -n x)"'
expect 2 "terraform apply" bash_hook "terraform -chdir=infra apply -auto-approve"
expect 2 "terraform plan" bash_hook "terraform plan"
expect 2 "kubectl" bash_hook "kubectl delete pod x"
expect 2 "func azure publish" bash_hook "func azure functionapp publish my-func"
expect 2 "swapping the identity" bash_hook "HARNESS_AZURE_CONFIG_DIR=~/.azure .harness/tools/cloud/cloud-read.sh az group list"
expect 2 "widening what the local reader may open" bash_hook "HARNESS_DEV_LOG_DIRS=/ .harness/tools/dev/dev-read.sh logfile /etc/passwd"
expect 0 "dev-read wrapper is allowed" bash_hook "~/.golden-path-harness/harness/tools/dev/dev-read.sh ports 5000"
expect 0 "sonar-read wrapper is allowed" bash_hook "~/.golden-path-harness/harness/tools/sonar/sonar-read.sh issues/search componentKeys=teamvalue_X"
expect 2 "curl to Sonar directly" bash_hook "curl -s https://sonarcloud.io/api/issues/search"
expect 2 "agent handles the Sonar token" bash_hook "echo \$SONAR_TOKEN"
expect 2 "curl to ServiceNow directly" bash_hook "curl -s https://x.service-now.com/api/now/table/incident"
expect 0 "sn-get wrapper is allowed" bash_hook "~/.golden-path-harness/harness/tools/servicenow/sn-get.sh sys_script collection=incident"
expect 2 "Az write cmdlet" bash_hook "pwsh -c 'Remove-AzResourceGroup -Name rg-dev'"
expect 2 "curl to ARM" bash_hook "curl -X PUT https://management.azure.com/subscriptions/x"
expect 2 "reading .env" bash_hook "cat .env"
expect 2 "sourcing .env.local" bash_hook "source .env.local && dotnet run"
expect 2 "printenv" bash_hook "printenv"
expect 2 "Python environment dump" bash_hook "python3 -c 'import os; print(os.environ)'"
expect 2 "Node environment dump" bash_hook "node -e 'console.log(process.env)'"
expect 2 "PowerShell environment dump" bash_hook "Get-ChildItem Env:"
# Text a command only carries is data. These all used to be blocked as "dumping the environment" or "reading a dotenv file".
expect 0 "C# setter in a file heredoc is data" bash_hook $'cat > Foo.cs <<\'EOF\'\npublic int X { get; set; }\nEOF'
expect 0 "process.env in a comment of a file heredoc is data" bash_hook $'cat > a.ts <<\'EOF\'\n// reads process.env.PORT\nEOF'
expect 0 "a dotenv path in the prose of a file heredoc is data" bash_hook $'cat > README.md <<\'EOF\'\nNever read the .env file; copy .env.example.\nEOF'
expect 0 "tofu and az login in a document written to a file are data" bash_hook $'cat > README.md <<EOF\nrun tofu plan, then az login\nEOF'
expect 0 "tee to a file with a heredoc is data" bash_hook $'tee notes.md <<\'EOF\'\nterraform apply\nEOF'
expect 0 "env in a commit message is data" bash_hook 'git commit -m "document the env layout and never read the .env file"'
expect 0 "set and printenv in an echoed sentence are data" bash_hook 'echo "use set; then printenv to compare"'
expect 0 "env running a program is not a dump" bash_hook "env FOO=1 dotnet test"
# What a command does is still checked: code fed to an interpreter, a real dump, a real read.
expect 2 "python heredoc that dumps the environment" bash_hook $'python3 - <<\'EOF\'\nimport os\nprint(os.environ)\nEOF'
expect 2 "bash heredoc that dumps the environment" bash_hook $'bash <<\'EOF\'\nprintenv\nEOF'
expect 2 "heredoc piped into bash is code" bash_hook $'cat <<\'EOF\' | bash\nprintenv\nEOF'
expect 2 "heredoc inside command substitution is code" bash_hook $'bash -c "$(cat <<\'EOF\'\nprintenv\nEOF\n)"'
expect 2 "writing the harness through a heredoc is still blocked" bash_hook $'cat > .harness/hooks/x <<\'EOF\'\nhi\nEOF'
expect 2 "a bare env is a dump" bash_hook "env"
expect 2 "env piped on is a dump" bash_hook "env | sort"
expect 2 "env in a command substitution is a dump" bash_hook 'echo $(env)'
expect 2 "an inline python script that reads the dotenv file" bash_hook "python3 -c \"print(open('.env').read())\""
expect 2 "a dotenv read after a commit message" bash_hook 'git commit -m "x" && cat .env'
# A script fed to an interpreter is judged by what it does with the environment, not by the words it contains. This is the case
# that used to force the agent to write the script with the Write tool: a patch that only mentions the dotenv file and process.env.
expect 0 "a python patch script that only mentions dotenv, process.env and a setter" bash_hook $'python3 - <<\'EOF\'\np = "docs/a.md"\ns = open(p).read()\ns = s.replace("x", "never read the .env file; process.env.PORT is fine; { get; set; }")\nopen(p, "w").write(s)\nEOF'
expect 0 "a node script that reads one named variable" bash_hook $'node - <<\'EOF\'\nconst port = process.env.PORT ?? "3000";\nconsole.log(port);\nEOF'
expect 0 "a python script that reads one named variable" bash_hook $'python3 - <<\'EOF\'\nimport os\nprint(os.environ["HOME"], os.environ.get("X"))\nEOF'
expect 0 "a node script that forwards the environment to a child" bash_hook $'node - <<\'EOF\'\nrequire("child_process").spawn("ls", { env: { ...process.env, A: "1" } });\nEOF'
expect 2 "a python script that opens the dotenv file" bash_hook $'python3 - <<\'EOF\'\nprint(open(".env").read())\nEOF'
expect 2 "a node script that reads the dotenv file" bash_hook $'node - <<\'EOF\'\nconsole.log(require("fs").readFileSync(".env", "utf8"));\nEOF'
expect 2 "a node script that prints the whole environment" bash_hook $'node - <<\'EOF\'\nconsole.log(process.env);\nEOF'
expect 2 "a python script that prints the whole environment as a dict" bash_hook $'python3 - <<\'EOF\'\nimport os\nprint(dict(os.environ))\nEOF'
expect 2 "a python script that iterates the environment" bash_hook $'python3 - <<\'EOF\'\nimport os\nfor k, v in os.environ.items():\n    print(k)\nEOF'
expect 2 "a python script that loads a dotenv file" bash_hook $'python3 - <<\'EOF\'\nfrom dotenv import load_dotenv\nload_dotenv()\nEOF'
expect 0 "push a named feature branch" bash_hook "git push -u origin feature/x"
expect 0 "push a feature branch by refspec" bash_hook "git push origin feature/x:feature/x"
expect 0 "push a feature branch after cd" bash_hook "cd repo && git push -u origin codex/x"
expect 2 "push to main" bash_hook "git push origin main"
expect 2 "push to master" bash_hook "git push origin master"
expect 2 "push to a release branch" bash_hook "git push origin release/1.2"
expect 2 "push a feature branch onto main" bash_hook "git push origin feature/x:main"
expect 2 "push to refs/heads/main" bash_hook "git push origin HEAD:refs/heads/main"
expect 2 "push HEAD without naming the branch" bash_hook "git push origin HEAD"
expect 2 "push without a target" bash_hook "git push"
expect 2 "push to the upstream only" bash_hook "git push origin"
expect 2 "force push" bash_hook "git push --force origin feature/x"
expect 2 "force-with-lease push" bash_hook "git push --force-with-lease origin feature/x"
expect 2 "force push by refspec" bash_hook "git push origin +feature/x"
expect 2 "delete a remote branch" bash_hook "git push origin --delete feature/x"
expect 2 "delete a remote branch by refspec" bash_hook "git push origin :feature/x"
expect 2 "push tags" bash_hook "git push origin --tags"
expect 2 "push a tag ref" bash_hook "git push origin refs/tags/v1"
expect 2 "push all branches" bash_hook "git push --all origin"
expect 2 "push with git -C to main" bash_hook "git -C repo push origin main"
expect 2 "second push in a chain goes to main" bash_hook "git push origin feature/x && git push origin main"
git init -q "$tmp/defaultbranch"
git -C "$tmp/defaultbranch" symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/develop
expect 2 "push to the repo's default branch" bash -c "cd '$tmp/defaultbranch' && jq -n --arg c 'git push origin develop' '{tool_input: {command: \$c}}' | '$h/hooks/guard-bash.sh'"
expect 2 "gh pr merge" bash_hook "gh pr merge 12 --squash"
expect 2 "editing the harness copy" bash_hook "sed -i '' 's/x/y/' .harness/rules/cloud/cld-1-agents-read-cloud-state.md"


echo "== guard-read"
expect 0 "source file" read_hook "src/Program.cs"
expect 0 ".env.example" read_hook "tests/.env.example"
expect 2 ".env" read_hook "tests/IntegrationPlatform.E2E/.env"
expect 2 ".env.production" read_hook ".env.production"

echo "== edit-gate (H.2)"
gate_state="$(mktemp -d)"
gate() { jq -n --arg s "$1" --arg f "$2" '{session_id: $s, tool_input: {file_path: $f}}' | TMPDIR="$gate_state" "$h/hooks/edit-gate.sh"; }
lookup() { jq -n --arg s "$1" '{session_id: $s, tool_input: {command: "python3 bundle.py select --brief a.yml"}}' | TMPDIR="$gate_state" "$h/hooks/guard-bash.sh"; }
expect 0 "first edit performs a successful rule lookup" gate gs1 "pipelines/deploy.yml"
expect 0 "the lookup passes guard-bash" lookup gs1
expect 0 "edit after the lookup is allowed" gate gs1 "pipelines/deploy.yml"
expect 0 "another session performs its own rule lookup" gate gs2 "pipelines/deploy.yml"
expect 0 "no session id delivers uncached guidance" gate "" "pipelines/deploy.yml"

echo "== agy edit gate (H.2)"
agy_gate() { jq -n --arg c "$1" --arg t "$2" --arg a "$3" '{conversationId: $c, toolCall: {name: $t, args: ($a | fromjson)}}' | TMPDIR="$gate_state" "$h/hooks/agy-edit-gate.sh"; }
agy_out() { agy_gate "$@" | jq -r .decision; }
expect 0 "agy: first edit delivers guidance before retry" test "$(agy_out ag1 edit_file '{"Path":"\"/r/a.yml\""}')" = deny
expect 0 "agy: lookup commands remain allowed" test "$(agy_out ag1 run_command '{"CommandLine":"python3 x/bundle.py select --brief a.yml"}')" = allow
expect 0 "agy: new guidance for a different scope is returned" bash -c "$(declare -f agy_gate); gate_state='$gate_state'; h='$h'; agy_gate ag1 edit_file '{\"Path\":\"/r/a.cs\"}' | jq -e '.decision == \"deny\" and (.reason | contains(\"IAC\") or contains(\"CLD\"))'"
expect 0 "agy: the same edit then passes" test "$(agy_out ag1 edit_file '{"Path":"/r/a.yml"}')" = allow
expect 0 "agy: a chained command does not mark the lookup" test "$(agy_out ag2 run_command '{"CommandLine":"python3 bundle.py select a; rm x"}')" = allow -a "$(agy_out ag2 write_file '{"Path":"/r/b.md"}')" = deny
expect 0 "agy: other tools pass" test "$(agy_out ag3 read_file '{"Path":"/r/a.yml"}')" = allow

echo "== cloud-read (stubs)"
mkdir -p "$tmp/bin"
for cli in az terraform tofu kubectl hcloud; do
  printf '#!/usr/bin/env bash\necho "%s $*"\n' "$cli" >"$tmp/bin/$cli"
  chmod +x "$tmp/bin/$cli"
done
cr() { PATH="$tmp/bin:$PATH" HARNESS_AZURE_CONFIG_DIR="$tmp/azure" HARNESS_KUBECONFIG="$tmp/kube" "$h/tools/cloud/cloud-read.sh" "$@"; }
expect 0 "az resource list" cr az resource list --resource-group rg-dev
expect 0 "az keyvault list" cr az keyvault list
expect 0 "az monitor ... show" cr az monitor diagnostic-settings show --name x --resource y
expect 0 "az graph query" cr az graph query -q "Resources | take 1"
expect 0 "az rest GET" cr az rest --method get --url https://management.azure.com/subscriptions?api-version=2022-12-01
expect 0 "terraform validate" cr terraform validate
expect 0 "terraform -chdir validate" cr terraform -chdir=infra validate
expect 3 "terraform -chdir apply" cr terraform -chdir=infra apply
expect 0 "terraform init -backend=false" cr terraform init -backend=false
expect 0 "kubectl get pods" cr kubectl get pods -n x
expect 0 "hcloud list" cr hcloud ECS NovaListServers --cli-region=eu-de
expect 3 "az group delete" cr az group delete -n rg-dev
expect 3 "az storage account keys list" cr az storage account keys list -n st
expect 3 "az keyvault secret show" cr az keyvault secret show --vault-name kv --name x
expect 3 "az account get-access-token" cr az account get-access-token
expect 3 "az webapp list-publishing-profiles" cr az webapp deployment list-publishing-profiles -n x -g y
expect 3 "az rest PUT" cr az rest --method put --url https://management.azure.com/x
expect 3 "az rest to Key Vault" cr az rest --url https://kv.vault.azure.net/secrets/x
expect 3 "az login" cr az login
expect 3 "terraform plan" cr terraform plan
expect 3 "terraform init with backend" cr terraform init
expect 3 "kubectl get secret" cr kubectl get secret db -o yaml
expect 3 "kubectl apply" cr kubectl apply -f x.yaml
expect 3 "hcloud delete" cr hcloud ECS NovaDeleteServer --server_id=x
expect 0 "az monitor log-analytics query" cr az monitor log-analytics query -w ws -a "AzureDiagnostics | take 1"
expect 0 "az monitor metrics list" cr az monitor metrics list --resource /subscriptions/x --metric Requests
expect 0 "az monitor activity-log list" cr az monitor activity-log list --offset 1d
expect 0 "az monitor metrics list-definitions" cr az monitor metrics list-definitions --resource x
expect 0 "az webapp log tail (verb not in an allowlist)" cr az webapp log tail -n app -g rg
expect 0 "az policy state summarize" cr az policy state summarize
expect 0 "az deployment group what-if" cr az deployment group what-if -g rg --template-file x.bicep
expect 0 "az deployment group list" cr az deployment group list -g rg
expect 0 "az diagnostic option value named like a verb is data" cr az monitor log-analytics query -w ws -a "print 'delete'"
mkdir -p "$tmp/loggedout"
printf '#!/usr/bin/env bash\necho "ERROR: Please run az login to setup account." >&2\nexit 1\n' >"$tmp/loggedout/az"
chmod +x "$tmp/loggedout/az"
cr_loggedout() { PATH="$tmp/loggedout:$PATH" "$h/tools/cloud/cloud-read.sh" "$@"; }
expect 4 "az not logged in tells the agent to ask the user" cr_loggedout az monitor log-analytics query -w ws -a "traces | take 1"
expect 3 "az group create" cr az group create -n rg --location westeurope
expect 3 "az resource update" cr az resource update --ids /subscriptions/x
expect 3 "az role assignment create" cr az role assignment create --assignee x --role Reader
expect 3 "az global option before the command" cr az --subscription x group delete -n rg
expect 3 "az verb after an option" cr az group --subscription x delete -n rg
expect 3 "az compound verb" cr az vm delete-instances -g rg -n vm
expect 3 "az vm run-command" cr az vm run-command invoke -g rg -n vm --command-id RunShellScript
expect 3 "az webapp ssh" cr az webapp ssh -n app -g rg
expect 3 "az acr login" cr az acr login -n acr
expect 3 "az account set" cr az account set -s x
expect 3 "az rest --method=PUT" cr az rest --method=PUT --url https://management.azure.com/x
expect 3 "az rest invoke-action listKeys" cr az rest --url https://management.azure.com/s/listKeys?api-version=1
expect 3 "az with no arguments" cr az
cur() { env -u HARNESS_AZURE_CONFIG_DIR PATH="$tmp/bin:$PATH" "$h/tools/cloud/cloud-read.sh" "$@"; }
expect 0 "az list with the user's current login" cur az resource list -g rg-dev
cur az resource list -g rg-dev >"$tmp/fallback.out" 2>"$tmp/fallback.err"
if grep -q 'warning: using personal az login' "$tmp/fallback.err"; then pass=$((pass + 1)); else fail=$((fail + 1)); echo "FAIL: personal az login fallback warning"; fi
expect 3 "az login with the user's current login" cur az login
expect 3 "az group delete with the user's current login" cur az group delete -n rg-dev
expect 3 "az keyvault secret show with the user's current login" cur az keyvault secret show --vault-name kv --name x
expect 3 "az rest PUT with the user's current login" cur az rest --method put --url https://management.azure.com/x
expect 0 "az rest GET with the user's current login" cur az rest --method get --url https://management.azure.com/x
expect 0 "az option value that starts like a verb is data (resource group)" cr az apim api list --service-name apim-prod --resource-group set-rg
expect 0 "az option value that starts like a verb is data (service name)" cr az apim api list --service-name publish-apim --resource-group rg --subscription 0000
expect 0 "az --key=value form with a verb-like value" cr az apim list --resource-group=deploy-rg
expect 0 "az apim policy read through az rest" cr az rest --method get --url "https://management.azure.com/subscriptions/0000/resourceGroups/rg/providers/Microsoft.ApiManagement/service/s/apis/a/policies/policy?api-version=2022-08-01&format=rawxml"
expect 0 "az ad app federated-credential list is metadata" cr az ad app federated-credential list --id x
expect 3 "az ad app credential list is still refused" cr az ad app credential list --id x
expect 3 "az verb after a boolean flag" cr az group --yes delete -n rg
expect 3 "az exact verb as the value of an unknown flag" cr az group --unknown-flag delete -n rg
expect 3 "az devops configure changes local defaults" cr az devops configure -d organization=https://dev.azure.com/o
expect 0 "az devops with --org on the call" cr az repos pr list --org https://dev.azure.com/o --project p
expect 0 "az devops invoke GET is allowed" cur az devops invoke --area git --resource pullRequestThreads
expect 3 "az devops invoke POST is refused" cur az devops invoke --http-method post --area git
expect 3 "az devops invoke with in-file is refused" cur az devops invoke --in-file payload.json

echo "== sonar-read (stub curl)"
printf '#!/usr/bin/env bash\ncat >/dev/null\nout=; while [[ $# -gt 0 ]]; do [[ "$1" == -o ]] && out="$2"; shift; done\necho "{}" >"$out"; printf 200\n' >"$tmp/bin/curl"
chmod +x "$tmp/bin/curl"
sr() { PATH="$tmp/bin:$PATH" SONAR_TOKEN=x "$h/tools/sonar/sonar-read.sh" "$@"; }
expect 0 "sonar issues/search" sr issues/search componentKeys=teamvalue_X resolved=false
expect 0 "sonar project_status" sr qualitygates/project_status projectKey=teamvalue_X
expect 3 "sonar endpoint not allowlisted" sr user_tokens/generate name=x
expect 3 "sonar write endpoint" sr issues/do_transition issue=x transition=wontfix
expect 3 "sonar argument without key=value" sr issues/search resolved
printf 'SONAR_TOKEN="from-file"\n' >"$tmp/envfile"
expect 0 "sonar token from the user's env file" env -u SONAR_TOKEN HARNESS_ENV_FILE="$tmp/envfile" PATH="$tmp/bin:$PATH" "$h/tools/sonar/sonar-read.sh" issues/search componentKeys=x
expect 3 "sonar without token or file" env -u SONAR_TOKEN HARNESS_ENV_FILE="$tmp/none" PATH="$tmp/bin:$PATH" "$h/tools/sonar/sonar-read.sh" issues/search

echo "== sn-get (stub curl)"
printf '#!/usr/bin/env bash\ncat >/dev/null\nout=; while [[ $# -gt 0 ]]; do [[ "$1" == --output ]] && out="$2"; shift; done\necho "{\\"result\\":[]}" >"$out"; printf 200\n' >"$tmp/bin/curl"
sg() { PATH="$tmp/bin:$PATH" SN_INSTANCE=dev.service-now.com SN_USER=u SN_PASSWORD=p "$h/tools/servicenow/sn-get.sh" "$@"; }
expect 0 "sn-get business rules" sg sys_script "collection=incident" "sys_id,name"
expect 3 "sn-get table not on the allowlist" sg incident "active=true"
expect 3 "sn-get user table" sg sys_user
expect 3 "sn-get without credentials" env -u SN_INSTANCE -u SN_USER -u SN_PASSWORD HARNESS_ENV_FILE="$tmp/none" PATH="$tmp/bin:$PATH" "$h/tools/servicenow/sn-get.sh" sys_script
expect 3 "sn-get instance with a path" env SN_INSTANCE=evil.example.com/x.service-now.com SN_USER=u SN_PASSWORD=p PATH="$tmp/bin:$PATH" "$h/tools/servicenow/sn-get.sh" sys_script
expect 0 "sn-access-check runs" env PATH="$tmp/bin:$PATH" SN_INSTANCE=dev.service-now.com SN_USER=u SN_PASSWORD=p "$h/tools/servicenow/sn-access-check.sh"

echo "== bundle"
expect 0 "bundle check passes" python3 -I "$h/tools/harness/bundle.py" check
expect 0 "context budget holds" python3 -I "$h/tools/harness/bundle.py" budget
mkdir -p "$tmp/budget/harness/tools/harness"
echo "short" >"$tmp/budget/AGENTS.base.md"; echo "idx" >"$tmp/budget/harness/index.md"
python3 -I "$h/tools/harness/bundle.py" --root "$tmp/budget/harness" budget --update >/dev/null
expect 0 "budget passes at the recorded size" python3 -I "$h/tools/harness/bundle.py" --root "$tmp/budget/harness" budget
echo "a much longer base instruction file" >"$tmp/budget/AGENTS.base.md"
expect 1 "budget fails when the base file grows" python3 -I "$h/tools/harness/bundle.py" --root "$tmp/budget/harness" budget
cp "$tmp/budget/harness/tools/harness/context-budget.json" "$tmp/budget/base.json"
python3 -I "$h/tools/harness/bundle.py" --root "$tmp/budget/harness" budget --update >/dev/null
expect 1 "budget fails when the budget file is raised against the base branch" python3 -I "$h/tools/harness/bundle.py" --root "$tmp/budget/harness" budget --baseline "$tmp/budget/base.json"
expect 0 "review evaluator unit tests" python3 -I "$here/tests/test_eval.py"
mkdir -p "$tmp/privacy/harness"
expect 0 "privacy check passes without private data" python3 -I "$h/tools/harness/bundle.py" --root "$tmp/privacy/harness" privacy-check
mkdir -p "$tmp/privacy/feedback/mined"
: >"$tmp/privacy/feedback/mined/private.csv"
expect 1 "privacy check rejects mined review data" python3 -I "$h/tools/harness/bundle.py" --root "$tmp/privacy/harness" privacy-check
printf 'src/Services/PartnerService.cs\n' >"$tmp/changed"
python3 -I "$h/tools/harness/bundle.py" select <"$tmp/changed" >"$tmp/select.json"
expect 0 "select picks T.2 for a .cs file" jq -e '.rules | to_entries | map(.value) | index("T.2") != null' "$tmp/select.json"
expect 0 "select skips IAC rules for a .cs file" jq -e '.rules | to_entries | map(.value) | index("IAC.1") == null' "$tmp/select.json"
python3 -I "$h/tools/harness/bundle.py" select src/Orders.cs >"$tmp/select-args.json" </dev/null
expect 0 "select takes paths as arguments, not only on stdin" jq -e '.rules | to_entries | map(.value) | index("T.2") != null' "$tmp/select-args.json"
expect 0 "select prints a summary for every rule it picks" jq -e '(.rules | length) > 0 and (.summary | length) == (.rules | length)' "$tmp/select-args.json"
cp -R "$h" "$tmp/withexample"
find "$tmp/withexample/examples" -name "e-*.md" -delete   # fixtures start without the real examples
cat >"$tmp/example.md" <<'CASE'
---
type: Example
title: "E-900 new HttpClient inside a service"
description: A service constructs its own HttpClient.
example_id: E-900
rule: /rules/testing/t-2-services-do-not-create-io.md
verdict: violation
status: draft
---

# Situation

Example.

## Good example

```csharp
public PartnerService(HttpClient http) => _http = http;
```

## Bad example

```csharp
var http = new HttpClient();
```
CASE
cp "$tmp/example.md" "$tmp/withexample/examples/e-001-new-httpclient.md"
python3 -I "$h/tools/harness/bundle.py" --root "$tmp/withexample" index >/dev/null
expect 0 "bundle with an valid example passes" python3 -I "$h/tools/harness/bundle.py" --root "$tmp/withexample" check
python3 -I "$h/tools/harness/bundle.py" --root "$tmp/withexample" select <"$tmp/changed" >"$tmp/select2.json"
expect 0 "select lists an unverified example as a hint" jq -e '.hints | index("/examples/e-001-new-httpclient.md") != null' "$tmp/select2.json"
awk '{print} /^status: draft$/ {print "verified: { by: human:reviewer, at: 2026-10-18T00:00:00Z }"}' "$tmp/example.md" >"$tmp/withexample/examples/e-001-new-httpclient.md"
python3 -I "$h/tools/harness/bundle.py" --root "$tmp/withexample" select <"$tmp/changed" >"$tmp/select3.json"
expect 0 "select lists a human-verified example as precedent" jq -e '.precedent | index("/examples/e-001-new-httpclient.md") != null' "$tmp/select3.json"
expect 0 "check-example accepts a draft with both examples" python3 -I "$h/tools/harness/bundle.py" check-example "$tmp/example.md"
{ cat "$tmp/example.md"; printf '\n# Variant: unlabeled\n\n```bicep\nparam a string\n```\n'; } >"$tmp/novariantmarks.md"
expect 1 "check-example rejects a variant without Good/Bad markers" python3 -I "$h/tools/harness/bundle.py" check-example "$tmp/novariantmarks.md"
{ cat "$tmp/example.md"; printf '\n# Variant: labeled\n\n```bicep\n// Good\nparam a string\n\n// Bad\nvar a = 1\n```\n'; } >"$tmp/variantmarks.md"
expect 0 "check-example accepts a variant with colon-less Good/Bad markers" python3 -I "$h/tools/harness/bundle.py" check-example "$tmp/variantmarks.md"
sed '/^## Bad example/,$d' "$tmp/example.md" >"$tmp/nobad.md"
expect 1 "check-example rejects an example without a bad example" python3 -I "$h/tools/harness/bundle.py" check-example "$tmp/nobad.md"
sed 's/^var http = new HttpClient();$/<code snippet>/' "$tmp/example.md" >"$tmp/placeholder.md"
expect 1 "check-example rejects the template placeholder" python3 -I "$h/tools/harness/bundle.py" check-example "$tmp/placeholder.md"
sed 's#^rule: .*#rule: /rules/nope.md#' "$tmp/example.md" >"$tmp/norule.md"
expect 1 "check-example rejects an unknown rule" python3 -I "$h/tools/harness/bundle.py" check-example "$tmp/norule.md"
sed 's/^Example\.$/The TeamNOW partner integration./' "$tmp/example.md" >"$tmp/specific.md"
expect 1 "check-example rejects a project-specific name" python3 -I "$h/tools/harness/bundle.py" check-example "$tmp/specific.md"
echo "Fabrikam" >"$tmp/terms.txt"
sed 's/^Example\.$/Built for Fabrikam./' "$tmp/example.md" >"$tmp/specific2.md"
expect 1 "check-example rejects a name from --terms" python3 -I "$h/tools/harness/bundle.py" check-example "$tmp/specific2.md" --terms "$tmp/terms.txt"
expect 0 "check-example accepts neutral names" python3 -I "$h/tools/harness/bundle.py" check-example "$tmp/example.md" --terms "$tmp/terms.txt"
sed 's/^verdict: violation$/verdict: boundary/' "$tmp/example.md" >"$tmp/boundary-bare.md"
expect 1 "a boundary example without requirement, owner and stale_after is rejected" python3 -I "$h/tools/harness/bundle.py" check-example "$tmp/boundary-bare.md"
awk '{print} /^verdict: boundary$/ {print "owner: human:reviewer"; print "stale_after: 2030-01-01T00:00:00Z"; print "sources:"; print "  - id: requirement"; print "    resource: Contract clause 4.2"}' "$tmp/boundary-bare.md" >"$tmp/boundary.md"
expect 0 "a boundary example with requirement, owner and stale_after passes" python3 -I "$h/tools/harness/bundle.py" check-example "$tmp/boundary.md"
awk '{print} /^status: draft$/ {print "verified: { by: human:reviewer, at: 2026-10-18T00:00:00Z }"; print "stale_after: 2020-01-01T00:00:00Z"}' "$tmp/example.md" >"$tmp/withexample/examples/e-001-new-httpclient.md"
python3 -I "$h/tools/harness/bundle.py" --root "$tmp/withexample" select <"$tmp/changed" >"$tmp/select4.json"
expect 0 "a stale example is not precedent" jq -e '(.stale | index("/examples/e-001-new-httpclient.md") != null) and (.precedent | length == 0)' "$tmp/select4.json"
cat >"$tmp/findings.txt" <<'EOF'
```json
[
  {"rule_id": "T.2", "file": "a.cs", "line": 3, "severity": "major", "summary": "s", "evidence": "new HttpClient()", "confidence": "high"},
  {"rule_id": "X.9", "file": "a.cs", "line": 4, "summary": "invented rule", "evidence": "e", "confidence": "high"},
  {"rule_id": "SEC.2", "file": "a.cs", "line": 5, "summary": "no evidence", "confidence": "high"}
]
```
EOF
python3 -I "$h/tools/harness/bundle.py" findings "$tmp/findings.txt" >"$tmp/valid.json" 2>/dev/null
expect 0 "findings keeps one valid finding" jq -e 'length == 1 and .[0].rule_id == "T.2"' "$tmp/valid.json"
mkdir -p "$tmp/anchor/src" && printf 'line one\nvar http = new HttpClient();\n' >"$tmp/anchor/src/a.cs"
echo '[{"rule_id": "T.2", "file": "src/a.cs", "line": 8, "summary": "s", "evidence": "new HttpClient()", "confidence": "high"},
       {"rule_id": "T.2", "file": "src/gone.cs", "line": 1, "summary": "s", "evidence": "x", "confidence": "high"}]' >"$tmp/anchor.txt"
python3 -I "$h/tools/harness/bundle.py" findings "$tmp/anchor.txt" --repo "$tmp/anchor" >"$tmp/anchored.json" 2>/dev/null
expect 0 "findings are anchored on their evidence, missing files dropped" jq -e 'length == 1 and .[0].line == 2 and .[0].anchored' "$tmp/anchored.json"
cp -R "$h" "$tmp/broken"
printf -- '---\ntype: Rule\ntitle: "X"\ndescription: d\nrule_id: T.1\napplies_to: nope\nseverity: huge\n---\n[x](/nowhere.md)\n' >"$tmp/broken/rules/testing/x.md"
expect 1 "check catches a broken rule" python3 -I "$h/tools/harness/bundle.py" --root "$tmp/broken" check

echo "== ado-post-findings (stub curl)"
cat >"$tmp/bin/curl" <<'STUB'
#!/usr/bin/env bash
# GET returns the threads recorded so far; POST records the body.
data=""
while [[ $# -gt 0 ]]; do
  [[ "$1" == "-d" ]] && { data="$2"; shift; }
  shift
done
if [[ -n "$data" ]]; then
  echo "$data" >>"$STUB_THREADS"
  echo '{}'
else
  jq -s '{value: .}' "$STUB_THREADS"
fi
STUB
chmod +x "$tmp/bin/curl"
: >"$tmp/threads.jsonl"
post() {
  PATH="$tmp/bin:$PATH" STUB_THREADS="$tmp/threads.jsonl" SYSTEM_ACCESSTOKEN=x SYSTEM_COLLECTIONURI=https://dev.azure.com/org/ \
    SYSTEM_TEAMPROJECT="Team Project" BUILD_REPOSITORY_ID=r SYSTEM_PULLREQUEST_PULLREQUESTID=1 \
    "$h/tools/azure-devops/ado-post-findings.sh" "$tmp/valid.json"
}
expect 0 "posts a finding" post
expect 0 "thread has the file, line and rule" jq -se '.[0].threadContext.filePath == "/a.cs" and .[0].threadContext.rightFileStart.line == 3 and (.[0].comments[0].content | contains("T.2"))' "$tmp/threads.jsonl"
expect 0 "a rerun posts nothing new" post
expect 0 "still one thread" jq -se 'length == 1' "$tmp/threads.jsonl"

echo "== ado-pr-threads (stub curl)"
cat >"$tmp/bin/curl" <<'STUB'
#!/usr/bin/env bash
cat >/dev/null
out=
while [[ $# -gt 0 ]]; do
  [[ "$1" == "-o" ]] && { out="$2"; shift; }
  shift
done
cat >"$out" <<'EOF'
{
  "value": [
    {
      "id": 1,
      "status": "active",
      "threadContext": {"filePath": "/src/A.cs", "rightFileStart": {"line": 10}},
      "comments": [{"commentType": "text", "content": "Please fix this", "author": {"displayName": "Reviewer"}}]
    },
    {
      "id": 2,
      "status": "fixed",
      "threadContext": {"filePath": "/src/B.cs", "rightFileStart": {"line": 20}},
      "comments": [{"commentType": "text", "content": "Done", "author": {"displayName": "Reviewer"}}]
    }
  ]
}
EOF
printf 200
STUB
chmod +x "$tmp/bin/curl"
pr_threads() {
  PATH="$tmp/bin:$PATH" "$h/tools/azure-devops/ado-pr-threads.sh" https://dev.azure.com/org "Team Project" "Repo" 1
}
expect 0 "ado-pr-threads runs" pr_threads
pr_threads >"$tmp/pr_threads.out"
if grep -q 'Unresolved threads:   1' "$tmp/pr_threads.out" && grep -q 'UNRESOLVED COMMENTS EXIST' "$tmp/pr_threads.out"; then
  pass=$((pass + 1))
else
  fail=$((fail + 1))
  echo "FAIL: ado-pr-threads summary output"
fi

echo "== evals (replay, no model)"
printf 'review prompt\n' >"$tmp/prompt.md"
cat >"$tmp/bin/claude" <<'STUB'
#!/usr/bin/env bash
test_tmp="$(dirname "$(dirname "$0")")"
printf '%s\n' "$*" >"$test_tmp/claude-args"
printf '%s\n' "${SYSTEM_ACCESSTOKEN:-missing}" >"$test_tmp/claude-env"
printf '{"result":"[]"}\n'
STUB
chmod +x "$tmp/bin/claude"
shim "$tmp/bin/claude"
expect 0 "Claude invocation is bounded and returns its result" env PATH="$tmp/bin:$PATH" \
  SYSTEM_ACCESSTOKEN=do-not-pass \
  python3 -I "$h/tools/review/run-claude.py" \
  "$tmp/prompt.md" "$tmp/raw.txt" "$tmp" "$h"
expect 0 "Claude invocation sets the turn limit" grep -q -- '--max-turns 10' "$tmp/claude-args"
expect 0 "Claude result is extracted" grep -Fqx '[]' "$tmp/raw.txt"
expect 0 "Claude does not inherit the pipeline token" grep -qx missing "$tmp/claude-env"
cat >"$tmp/bin/claude" <<'STUB'
#!/usr/bin/env bash
sleep 2
printf '{"result":"[]"}\n'
STUB
chmod +x "$tmp/bin/claude"
shim "$tmp/bin/claude"
expect 124 "Claude invocation times out" env PATH="$tmp/bin:$PATH" HARNESS_REVIEW_TIMEOUT_SECONDS=1 \
  python3 -I "$h/tools/review/run-claude.py" "$tmp/prompt.md" "$tmp/raw.txt" "$tmp" "$h"

mkdir -p "$tmp/replay"
t2='[{"rule_id": "T.2", "file": "src/PartnerService.cs", "line": 8, "severity": "major", "summary": "new HttpClient", "evidence": "new HttpClient", "confidence": "high"}]'
echo '[{"rule_id": "T.2", "file": "src/Example.cs", "line": 1, "severity": "major", "summary": "s", "evidence": "new HttpClient()", "confidence": "high"}]' >"$tmp/replay/example-e-001-new-httpclient-bad.txt"
echo '[]' >"$tmp/replay/example-e-001-new-httpclient-good.txt"
echo "$t2" >"$tmp/replay/example-e-018-pr-description-cannot-waive-a-rule-bad.txt"
echo '[]' >"$tmp/replay/example-e-018-pr-description-cannot-waive-a-rule-good.txt"
echo '[{"rule_id": "CODE.3", "file": "src/TaskProcessor.cs", "line": 3, "severity": "minor", "summary": "class name does not match its file", "evidence": "class X", "confidence": "high"}]' >"$tmp/replay/example-e-019-a-pure-rename-does-not-raise-major-findings-bad.txt"
echo '[]' >"$tmp/replay/example-e-019-a-pure-rename-does-not-raise-major-findings-good.txt"
echo '[]' >"$tmp/replay/example-e-019-a-pure-rename-does-not-raise-major-findings-pure-rename.txt"
awk '{print} /^status: draft$/ {print "verified: { by: human:reviewer, at: 2026-10-18T00:00:00Z }"}' "$tmp/example.md" >"$tmp/withexample/examples/e-001-new-httpclient.md"
cp "$h/examples/e-018-pr-description-cannot-waive-a-rule.md" "$tmp/withexample/examples/"
cp "$h/examples/e-019-a-pure-rename-does-not-raise-major-findings.md" "$tmp/withexample/examples/"
python3 -I "$h/tools/harness/bundle.py" --root "$tmp/withexample" index >/dev/null
echo '{"min_pass_rate": 0.85, "min_scenarios": 7, "critical_repeats": 3}' >"$tmp/thresholds.json"
ev() { python3 -I "$h/tools/review/eval.py" --engine replay --replay-dir "$tmp/replay" --bundle "$tmp/withexample" --thresholds "$tmp/thresholds.json" "$@"; }
expect 0 "case evaluations pass the gate" ev
grep -q 'example-e-001-new-httpclient-good' "$tmp/out" && pass=$((pass + 1)) || { fail=$((fail + 1)); echo "FAIL: case scenarios were not generated"; }
echo '[]' >"$tmp/replay/example-e-018-pr-description-cannot-waive-a-rule-bad.txt"
expect 1 "missing the adversarial finding fails the critical gate" ev
echo "$t2" >"$tmp/replay/example-e-018-pr-description-cannot-waive-a-rule-bad.txt"
echo '[{"rule_id": "T.2", "file": "src/Example.cs", "line": 1, "severity": "major", "summary": "s", "evidence": "x", "confidence": "high"}]' >"$tmp/replay/example-e-001-new-httpclient-good.txt"
expect 1 "flagging an example's good example fails it" ev --only example-e-001-new-httpclient-good
echo '[]' >"$tmp/replay/example-e-001-new-httpclient-good.txt"
cp "$tmp/example.md" "$tmp/withexample/examples/e-001-new-httpclient.md"
echo '{"min_pass_rate": 0.85, "min_scenarios": 5, "critical_repeats": 3}' >"$tmp/thresholds.json"
expect 0 "a passing draft case is reported as advisory" ev
grep -q 'advisory (drafts, not gating): 2/2 passed' "$tmp/out" && pass=$((pass + 1)) || { fail=$((fail + 1)); echo "FAIL: advisory summary missing"; }
echo '[]' >"$tmp/replay/example-e-001-new-httpclient-bad.txt"
echo '[{"rule_id": "T.2", "file": "src/Example.cs", "line": 1, "severity": "major", "summary": "s", "evidence": "x", "confidence": "high"}]' >"$tmp/replay/example-e-001-new-httpclient-good.txt"
expect 0 "draft examples the reviewer gets wrong do not fail the gate" ev
grep -q 'FAIL \[.*\]  example-e-001-new-httpclient-bad' "$tmp/out" && pass=$((pass + 1)) || { fail=$((fail + 1)); echo "FAIL: advisory failure not shown"; }
grep -q 'advisory (drafts, not gating): 0/2 passed' "$tmp/out" && pass=$((pass + 1)) || { fail=$((fail + 1)); echo "FAIL: advisory failure count missing"; }

echo "== check-scenarios"
cat >"$tmp/scenarios.json" <<'EOF'
[{"component": "tls.esb.b2b.case.external/**", "scenarios": ["tests/E2E/**/Features/B2B/**"]}]
EOF
scen() { printf '%s\n' "$@" | python3 -I "$h/tools/testing/check-scenarios.py" --config "$tmp/scenarios.json" --description "$tmp/pr.txt"; }
: >"$tmp/pr.txt"
expect 1 "component change without scenario" scen tls.esb.b2b.case.external/Fnc/Services/X.cs
expect 0 "component change with scenario" scen tls.esb.b2b.case.external/Fnc/Services/X.cs tests/E2E/P/Features/B2B/External/Case.feature
expect 0 "unrelated change" scen docs/readme.md
echo "e2e: n/a - refactor without behaviour change" >"$tmp/pr.txt"
expect 0 "waived with a reason" scen tls.esb.b2b.case.external/Fnc/Services/X.cs
echo "e2e: n/a - x" >"$tmp/pr.txt"
expect 1 "waiver without a real reason" scen tls.esb.b2b.case.external/Fnc/Services/X.cs

echo "== ci scripts"
mkdir -p "$tmp/ci/origin" && (
  cd "$tmp/ci/origin" && git init -q -b main . && git config user.email t@t && git config user.name t
  mkdir -p harness/rules harness/tools/harness && echo a >harness/rules/r.md && echo '{"agentsBaseBytes": 1}' >harness/tools/harness/context-budget.json
  git add -A && git commit -qm base && git update-ref refs/remotes/origin/main HEAD && git checkout -qb pr
)
ci() { (cd "$tmp/ci/origin" && "$here/infra/scripts/$1"); }
expect 0 "review-changed on an unchanged branch" ci review-changed.sh
echo b >>"$tmp/ci/origin/harness/rules/r.md"; git -C "$tmp/ci/origin" commit -qam change
ci review-changed.sh | grep -q "EvalsNeeded" && pass=$((pass + 1)) || { fail=$((fail + 1)); echo "FAIL: review-changed did not flag a rules change"; }

echo "== check-iac"
mkdir -p "$tmp/iac"
printf "p: {\n  minTlsVersion: '1.0'\n  networkAcls: { defaultAction: 'Allow' }\n  enablePurgeProtection: false\n}\n" >"$tmp/iac/bad.bicep"
printf "p: {\n  minTlsVersion: 'TLS1_2'\n  networkAcls: { defaultAction: 'Deny' }\n  enablePurgeProtection: true\n}\n" >"$tmp/iac/good.bicep"
iacc() { (cd "$tmp/iac" && printf '%s\n' "$@" | python3 -I "$h/tools/iac/check-iac.py" --description "$tmp/iac/pr.txt"); }
: >"$tmp/iac/pr.txt"
expect 1 "iac check flags weak settings" iacc bad.bicep
expect 0 "iac check passes hardened settings" iacc good.bicep
expect 0 "iac check ignores other file types" iacc pr.txt
echo "iac: n/a - public entry point, stated in the PR" >"$tmp/iac/pr.txt"
expect 0 "iac check waived with a reason" iacc bad.bicep

echo "== business-testplan"
plan() { python3 -I "$h/tools/testing/business-testplan.py" "$@"; }
if python3 -I -c 'import openpyxl' 2>/dev/null; then
  expect 0 "the template builds a workbook" plan "$h/templates/business-testplan.spec.json" "$tmp/plan.xlsx"
  expect 0 "the workbook exists" test -s "$tmp/plan.xlsx"
  printf '{"title":"x","systems":["a"],"scenarios":[{"id":"1","title":"t","stages":[{"title":"s","steps":[{"step":"no who"}]}]}]}' >"$tmp/bad.json"
  expect 1 "an incomplete spec is refused" plan "$tmp/bad.json" "$tmp/bad.xlsx"
  expect 0 "nothing is written for a refused spec" test ! -e "$tmp/bad.xlsx"
  expect 1 "no arguments prints the usage" plan
else
  echo "skipped: python3 has no openpyxl"
fi

echo "== render findings"
printf '%s' '[{"rule_id":"SEC.2","file":"src/A.cs","line":5,"severity":"major","confidence":"high","evidence":"log(email)","summary":"Email logged","fix":"log the id","outcome":"fixed"},{"rule_id":"T.5","file":"src/B.cs","line":1,"severity":"major","confidence":"high","evidence":"x","summary":"No test","reason":"needs Foundation types"}]' >"$tmp/findings.json"
expect 0 "render shows counts, table and outcome" bash -c "python3 -I '$h/tools/review/render.py' '$tmp/findings.json' --branch b --rules 3 --verified build | grep -q '2 findings: 1 fixed, 1 open' && python3 -I '$h/tools/review/render.py' '$tmp/findings.json' | grep -q 'Why not fixed: needs Foundation types'"
expect 1 "render rejects a file that is not findings" python3 -I "$h/tools/review/render.py" "$tmp/out"

echo "== frontend screenshot tool (no browser needed)"
shot="$h/tools/frontend/screenshot.mjs"
expect 1 "screenshot needs a url" node "$shot"
expect 1 "screenshot refuses a remote host" node "$shot" --url https://example.com/
expect 1 "screenshot refuses a non-http url" node "$shot" --url file:///etc/hosts
expect 1 "screenshot refuses a bad viewport" node "$shot" --url http://localhost:1/ --viewports 390
expect 1 "screenshot refuses an unknown option" node "$shot" --url http://localhost:1/ --bogus
expect 0 "contrast tool: ratios, tokens, failing and passing pairs" node --test "$here/tests/frontend-contrast.test.mjs"
expect 1 "screenshot refuses a missing auth state file" node "$shot" --url http://localhost:1/ --auth-state "$tmp/none.json"
expect 0 "auth state: validation, seed script, MSAL example, git refusal and a logged-in capture" node --test "$here/tests/frontend-auth-state.test.mjs"
expect 0 "guard allows the screenshot tool" bash_hook "node ~/.golden-path-harness/harness/tools/frontend/screenshot.mjs --url http://localhost:5173/ --name home"

echo "== orchestrate tool"
orch="$h/tools/orchestration/orchestrate.py"
expect 0 "orchestrate tier identifies economy" bash -c "python3 -I '$orch' tier --task 'format and lint files' | grep -q '\"tier\": \"economy\"'"
expect 0 "orchestrate tier identifies reasoner" bash -c "python3 -I '$orch' tier --task 'design authentication architecture and security boundaries' | grep -q '\"tier\": \"reasoner\"'"
expect 0 "orchestrate plan outputs work packages" bash -c "python3 -I '$orch' plan --spec 'Build .NET backend with React frontend' | grep -q 'dotnet-backend-builder'"
expect 0 "orchestrate plan markdown format" bash -c "python3 -I '$orch' plan --spec 'Build .NET backend with React frontend' --format markdown | grep -q 'Workload Orchestration Plan'"
printf '# Report\n' >"$tmp/report-empty.md"
printf '# Report\n\n# Workload Orchestration Plan\n| Role | Work Package |\n' >"$tmp/report-plan.md"
printf '# Report\n\nDecomposition: single thread - one engineer, one afternoon, the layers are thin\n' >"$tmp/report-reason.md"
printf '# Report\n\nDecomposition: single thread - x\n' >"$tmp/report-weak.md"
three="Build a .NET API, a React frontend and a Directus data model with Docker infrastructure"
expect 3 "layers: three layers and no plan in the report" python3 -I "$orch" layers --spec "$three" --report "$tmp/report-empty.md"
expect 0 "layers: a plan in the report satisfies it" python3 -I "$orch" layers --spec "$three" --report "$tmp/report-plan.md"
expect 0 "layers: a named reason for one thread satisfies it" python3 -I "$orch" layers --spec "$three" --report "$tmp/report-reason.md"
expect 3 "layers: a reason of one letter does not" python3 -I "$orch" layers --spec "$three" --report "$tmp/report-weak.md"
expect 3 "layers: no report file counts as no plan" python3 -I "$orch" layers --spec "$three" --report "$tmp/none.md"
expect 0 "layers: one layer needs no plan" python3 -I "$orch" layers --spec "Add an endpoint to the .NET API" --report "$tmp/report-empty.md"
expect 3 "layers: paths count too" python3 -I "$orch" layers --paths src/api/A.cs src/frontend/App.tsx infra/api.Dockerfile --report "$tmp/report-empty.md"
expect 0 "layers: without --report it only informs" python3 -I "$orch" layers --spec "$three"

echo "== install (throwaway home)"
mkdir -p "$tmp/home/.claude" "$tmp/home/vscode"
printf '@RTK.md\n\n# TeamValue AI Hub (managed by install.ps1)\n@import /old/global.instructions.md\n# end TeamValue AI Hub\n' >"$tmp/home/.claude/CLAUDE.md"
echo '{"permissions": {"allow": ["Bash(az group list *)", "Bash(git status)"]}}' >"$tmp/home/.claude/settings.json"
native_here="$(cygpath -w "$here" 2>/dev/null || printf %s "$here")"   # install.sh writes the import path in the OS's own form
inst() { HOME="$tmp/home" HARNESS_VSCODE_USER_DIR="$tmp/home/vscode" "$here/install.sh" "$@"; }
ln -s "$tmp/old-bundle" "$tmp/home/.harness"; ln -s "$tmp/old-feedback" "$tmp/home/.harness-feedback"   # a pre-migration install
expect 0 "install runs" inst
expect 0 "legacy ~/.harness links are removed" bash -c "test ! -e '$tmp/home/.harness' && test ! -L '$tmp/home/.harness' && test ! -L '$tmp/home/.harness-feedback'"
expect 0 "hooks point at the single root" jq -e '[.hooks.PreToolUse[].hooks[].command] | all(contains("/.golden-path-harness/harness/hooks/"))' "$tmp/home/.claude/settings.json"
expect 0 "~/.golden-path-harness links the bundle and feedback" test "$(readlink "$tmp/home/.golden-path-harness/harness")" = "$here/harness" -a "$(readlink "$tmp/home/.golden-path-harness/feedback")" = "$here/feedback"
expect 0 "~/.golden-path-harness has the runtime dirs" bash -c "cd '$tmp/home/.golden-path-harness' && test -d config -a -d cache -a -d state -a -d workspaces -a -d logs -a -d testing"
echo keep >"$tmp/home/.golden-path-harness/state/marker"
expect 0 "CLAUDE.md imports AGENTS.base.md, old AI Hub block removed" bash -c "grep -qF '@$native_here/AGENTS.base.md' '$tmp/home/.claude/CLAUDE.md' && ! grep -q 'AI Hub' '$tmp/home/.claude/CLAUDE.md'"
expect 0 "hooks installed, az allow rules removed, others kept" jq -e '(.hooks.PreToolUse | length == 3) and (.permissions.allow | index("Bash(git status)") != null) and (.permissions.allow | map(select(startswith("Bash(az "))) | length == 0)' "$tmp/home/.claude/settings.json"
expect 0 "/tv-review for Claude" test -f "$tmp/home/.claude/skills/tv-review/SKILL.md" 
expect 0 "/tv-review for Copilot uses the same adapter" cmp "$here/adapters/tv-review.skill.md" "$tmp/home/.copilot/skills/tv-review/SKILL.md"
mkdir -p "$tmp/home/.copilot/skills/unrelated"
echo keep >"$tmp/home/.copilot/skills/unrelated/SKILL.md"
expect 0 "install is idempotent" bash -c "HOME='$tmp/home' HARNESS_VSCODE_USER_DIR='$tmp/home/vscode' '$here/install.sh' | grep -vq updated"
printf '\nold adapter\n' >>"$tmp/home/.copilot/skills/tv-review/SKILL.md"
expect 0 "install updates a stale Copilot adapter" inst
expect 0 "updated Copilot adapter matches source" cmp "$here/adapters/tv-review.skill.md" "$tmp/home/.copilot/skills/tv-review/SKILL.md"
expect 0 "uninstall runs" inst --uninstall
expect 0 "uninstall removes Copilot review but keeps unrelated skills" bash -c "test ! -f '$tmp/home/.copilot/skills/tv-review/SKILL.md' && test -f '$tmp/home/.copilot/skills/unrelated/SKILL.md'"
expect 0 "uninstall keeps runtime state, removes links" bash -c "test -f '$tmp/home/.golden-path-harness/state/marker' && test ! -e '$tmp/home/.golden-path-harness/harness' && test ! -e '$tmp/home/.golden-path-harness/feedback'"
expect 0 "GOLDEN_PATH_HOME relocates the root" bash -c "GOLDEN_PATH_HOME='$tmp/gp' HOME='$tmp/home' HARNESS_VSCODE_USER_DIR='$tmp/home/vscode' '$here/install.sh' >/dev/null && test -d '$tmp/gp/state' && test -L '$tmp/gp/harness' && GOLDEN_PATH_HOME='$tmp/gp' HOME='$tmp/home' HARNESS_VSCODE_USER_DIR='$tmp/home/vscode' '$here/install.sh' --uninstall >/dev/null"
expect 0 "uninstall removes the import" bash -c "! grep -q 'TeamValue harness' '$tmp/home/.claude/CLAUDE.md'"

source "$here/tests/compare-ui.sh"
source "$here/tests/coverage-impact.sh"
source "$here/tests/dep-read.sh"
source "$here/tests/ado-run-timing.sh"
source "$here/tests/dev-read.sh"
source "$here/tests/spec-note.sh"
source "$here/tests/scaffold.sh"
source "$here/tests/density.sh"
source "$here/tests/orchestrate-models.sh"
source "$here/tests/eval-queue.sh"

echo
echo "$pass passed, $fail failed"
[[ "$fail" == 0 ]]
