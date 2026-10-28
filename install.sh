#!/usr/bin/env bash
# Install the harness for your user, so it applies in every repo. This repo stays the only source: nothing is
# copied into project repos.
#
# Usage:   ./install.sh            install, or update after a git pull (idempotent)
#          ./install.sh --uninstall
#
# Installs:
#   ~/.harness                  symlink to this repo's harness/ (bundle, tools, hooks, templates)
#   ~/.harness-feedback         symlink to this repo's feedback/: draft cases from every repo land here
#   ~/.claude/CLAUDE.md         a marked block that imports AGENTS.base.md
#   ~/.claude/settings.json     the guard hooks, the Stop verify, an allow rule for cloud-read.sh
#   ~/.claude/skills/example/   /example for Claude Code
#   ~/.claude/skills/tv-review/ /tv-review for Claude Code
#   VS Code user prompts        teamvalue.instructions.md and example.prompt.md for Copilot
# Removes the old AI Hub wiring: its CLAUDE.md/AGENTS.md import block, its Claude marketplace and plugin, and
# its VS Code marketplace entry. Bash(az ...) allow rules are removed too: the guard blocks az outside
# cloud-read.sh (CLD.1), and `az account get-access-token` returns a token.
# Every file it changes is backed up next to itself as <file>.bak-harness-<timestamp>.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
mode="${1:-install}"
stamp="$(date +%Y%m%d%H%M%S)"

case "$(uname -s)" in
  Darwin) vscode="$HOME/Library/Application Support/Code/User" ;;
  MINGW* | MSYS* | CYGWIN*) vscode="${APPDATA:-$HOME/AppData/Roaming}/Code/User" ;;
  *) vscode="$HOME/.config/Code/User" ;;
esac
vscode="${HARNESS_VSCODE_USER_DIR:-$vscode}"

python3 -I - "$mode" "$here" "$HOME" "$vscode" "$stamp" <<'PY'
import json, pathlib, re, shutil, subprocess, sys

mode, here, home, vscode, stamp = sys.argv[1:]
here, home, vscode = pathlib.Path(here), pathlib.Path(home), pathlib.Path(vscode)
install = mode == "install"
if mode not in ("install", "--uninstall"):
    sys.exit(f"install.sh: unknown option {mode}")

OLD_BLOCK = re.compile(r"\n?# TeamValue AI Hub \(managed by install\.ps1\)\n.*?# end TeamValue AI Hub\n?", re.S)
NEW_BLOCK = re.compile(r"\n?# TeamValue harness \(managed by install\.sh\)\n.*?# end TeamValue harness\n?", re.S)
HOOK_MARK = "/.harness/hooks/"
CLOUD_READ = [
    f"Bash({home}/.harness/tools/cloud/cloud-read.sh *)", "Bash(~/.harness/tools/cloud/cloud-read.sh *)",
    f"Bash({home}/.harness/tools/sonar/sonar-read.sh *)", "Bash(~/.harness/tools/sonar/sonar-read.sh *)",
    f"Bash({home}/.harness/tools/servicenow/sn-get.sh *)", "Bash(~/.harness/tools/servicenow/sn-get.sh *)",
    f"Bash({home}/.harness/tools/servicenow/sn-access-check.sh)", "Bash(~/.harness/tools/servicenow/sn-access-check.sh)",
]
# allow rules from before tools/ was grouped by domain; drop them so only the current paths stay allowed
LEGACY_CLOUD_READ = [a.replace("tools/cloud/", "tools/").replace("tools/sonar/", "tools/") for a in CLOUD_READ]


def backup(path):
    if path.exists():
        shutil.copy2(path, path.with_name(f"{path.name}.bak-harness-{stamp}"))


def write(path, text):
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"updated {path}")


# ~/.harness
link = home / ".harness"
if link.is_symlink() or not link.exists():
    if link.is_symlink():
        link.unlink()
    if install:
        link.symlink_to(here / "harness", target_is_directory=True)
        print(f"linked {link} -> {here / 'harness'}")
else:
    sys.exit(f"install.sh: {link} exists and is not a symlink; move it away first")

feedback_link = home / ".harness-feedback"
(here / "feedback").mkdir(exist_ok=True)
if feedback_link.is_symlink():
    feedback_link.unlink()
if install and not feedback_link.exists():
    feedback_link.symlink_to(here / "feedback", target_is_directory=True)
    print(f"linked {feedback_link} -> {here / 'feedback'}")

# CLAUDE.md and AGENTS.md in the home folder: drop the old AI Hub block, add ours to CLAUDE.md
for path, ours in ((home / ".claude" / "CLAUDE.md", True), (home / "AGENTS.md", False)):
    if not path.exists() and not (install and ours):
        continue
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    text = NEW_BLOCK.sub("\n", OLD_BLOCK.sub("\n", text)).rstrip("\n") + "\n"
    if install and ours:
        text += (f"\n# TeamValue harness (managed by install.sh)\n@{here}/AGENTS.base.md\n"
                 f"If the text `tvh-loaded` is not in your context, the import failed: read {here}/AGENTS.base.md once.\n"
                 "# end TeamValue harness\n")
    write(path, text.lstrip("\n"))

# ~/.claude/settings.json
settings_path = home / ".claude" / "settings.json"
settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
before = json.dumps(settings, indent=2)
hooks = settings.setdefault("hooks", {})
for event in ("PreToolUse", "Stop"):
    hooks[event] = [g for g in hooks.get(event, [])
                    if not any(HOOK_MARK in h.get("command", "") for h in g.get("hooks", []))]
if install:
    hook = lambda name: {"type": "command", "command": f'"$HOME"/.harness/hooks/{name}'}
    hooks["PreToolUse"] += [{"matcher": "Bash", "hooks": [hook("guard-bash.sh")]},
                            {"matcher": "Read|Grep|Glob", "hooks": [hook("guard-read.sh")]}]
    hooks["Stop"] += [{"hooks": [hook("stop-verify.sh")]}]
for event in [e for e, groups in hooks.items() if not groups]:
    del hooks[event]
perms = settings.setdefault("permissions", {})
allow = perms.get("allow", [])
removed = [a for a in allow if re.match(r"Bash\(az[ :]", a)]
allow = [a for a in allow if a not in removed and a not in CLOUD_READ and a not in LEGACY_CLOUD_READ]
if install:
    allow += CLOUD_READ
perms["allow"] = allow
for key in [k for k in settings.get("enabledPlugins", {}) if "teamvalue-aihub" in k]:
    del settings["enabledPlugins"][key]
settings.get("extraKnownMarketplaces", {}).pop("teamvalue-aihub", None)
if json.dumps(settings, indent=2) != before:
    write(settings_path, json.dumps(settings, indent=2) + "\n")
for a in removed:
    print(f"removed allow rule {a} (CLD.1: use ~/.harness/tools/cloud/cloud-read.sh)")

# Claude's own plugin state for the old AI Hub
for name in ("known_marketplaces.json", "installed_plugins.json"):
    path = home / ".claude" / "plugins" / name
    if not path.exists():
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    container = data.get("plugins", data) if isinstance(data, dict) else data
    if isinstance(container, dict):
        stale = [k for k in container if "teamvalue-aihub" in k]
        for k in stale:
            del container[k]
        if stale:
            write(path, json.dumps(data, indent=2) + "\n")

# /example and /tv-review for Claude Code
for name in ("example", "tv-review"):
    skill = home / ".claude" / "skills" / name / "SKILL.md"
    if install:
        write(skill, (here / f"adapters/{name}.skill.md").read_text(encoding="utf-8"))
    elif skill.exists():
        skill.unlink()
        print(f"removed {skill}")
# Remove legacy orchestrate skill if present
stale_orchestrate = home / ".claude" / "skills" / "orchestrate"
if stale_orchestrate.exists():
    shutil.rmtree(stale_orchestrate, ignore_errors=True)

# Copilot in VS Code: user-level instructions and prompt files, and the old marketplace entry
if vscode.exists():
    prompts = vscode / "prompts"
    instructions = prompts / "teamvalue.instructions.md"
    example = prompts / "example.prompt.md"
    stale_prompt = prompts / "orchestrate.prompt.md"
    if stale_prompt.exists():
        stale_prompt.unlink()
    if install:
        version = subprocess.run(["git", "-C", str(here), "describe", "--tags", "--always", "--dirty"],
                                 capture_output=True, text=True).stdout.strip() or "unknown"
        header = ("---\napplyTo: '**'\ndescription: TeamValue harness rules. Generated by install.sh; do not edit.\n---\n\n"
                  f"<!-- harness version: {version} -->\n\n")
        write(instructions, header + (here / "AGENTS.base.md").read_text(encoding="utf-8"))
        write(example, (here / "adapters/example.prompt.md").read_text(encoding="utf-8"))
    else:
        for f in (instructions, example):
            if f.exists():
                f.unlink()
                print(f"removed {f}")
    user_settings = vscode / "settings.json"
    if user_settings.exists():
        text = user_settings.read_text(encoding="utf-8")
        cleaned = re.sub(r'^\s*"chat\.plugins\.marketplaces"\s*:\s*"[^"\n]*TeamValue\.AiHub[^"\n]*",?\s*\n', "", text, flags=re.M)
        if cleaned != text:
            write(user_settings, cleaned)

print("install.sh: done" if install else "install.sh: uninstalled")
PY
