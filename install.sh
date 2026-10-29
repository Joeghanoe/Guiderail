#!/usr/bin/env bash
# Install the harness for your user, so it applies in every repo. This repo stays the only source: nothing is
# copied into project repos.
#
# Usage:   ./install.sh            install, or update after a git pull (idempotent)
#          ./install.sh --uninstall
#
# Installs:
#   ~/.golden-path-harness/     the one harness-owned root (override with GOLDEN_PATH_HOME):
#     harness, feedback         links to this repo's harness/ and feedback/
#     config cache state workspaces logs   mutable runtime state; never touched by update or uninstall
# Removes the legacy ~/.harness and ~/.harness-feedback links (and their hook/allow entries) when it finds them.
#   ~/.claude/CLAUDE.md         a marked block that imports AGENTS.base.md
#   ~/.claude/settings.json     the guard hooks, the Stop verify, an allow rule for cloud-read.sh
#   ~/.claude/skills/tv-review/ /tv-review for Claude Code
#   VS Code user prompts        teamvalue.instructions.md for Copilot
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

# python.org's Windows installer provides `python`, not `python3`; the Store stub for python3 exits non-zero.
py=python3
"$py" -c '' >/dev/null 2>&1 || py=python
command -v "$py" >/dev/null 2>&1 || { echo "install.sh: Python 3 is required (macOS: brew install python; Windows: winget install Python.Python.3.12)." >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "install.sh: jq is required by the hooks and tools (macOS: brew install jq; Windows: winget install jqlang.jq)." >&2; exit 1; }

"$py" -I - "$mode" "$here" "$HOME" "$vscode" "$stamp" <<'PY'
import json, os, pathlib, re, shutil, subprocess, sys

mode, here, home, vscode, stamp = sys.argv[1:]
here, home, vscode = pathlib.Path(here), pathlib.Path(home), pathlib.Path(vscode)
install = mode == "install"
if mode not in ("install", "--uninstall"):
    sys.exit(f"install.sh: unknown option {mode}")

OLD_BLOCK = re.compile(r"\n?# TeamValue AI Hub \(managed by install\.ps1\)\n.*?# end TeamValue AI Hub\n?", re.S)
NEW_BLOCK = re.compile(r"\n?# TeamValue harness \(managed by install\.sh\)\n.*?# end TeamValue harness\n?", re.S)
HOOK_MARKS = ("/.harness/hooks/", "/.golden-path-harness/harness/hooks/")
gp_home = pathlib.Path(os.getenv("GOLDEN_PATH_HOME") or home / ".golden-path-harness")
TOOLS = ("cloud/cloud-read.sh *", "sonar/sonar-read.sh *", "servicenow/sn-get.sh *", "servicenow/sn-access-check.sh")
CLOUD_READ = [f"Bash({base}/harness/tools/{t})" for t in TOOLS for base in (gp_home, "~/.golden-path-harness")]
# allow rules from earlier layouts (~/.harness, tools/ before it was grouped by domain); drop them
LEGACY_CLOUD_READ = [f"Bash({base}/.harness/tools/{t})" for t in TOOLS for base in (home, "~")] + \
                    [f"Bash({base}/.harness/tools/{t.split('/', 1)[1]})" for t in TOOLS for base in (home, "~")]


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


def is_link(path):
    return path.is_symlink() or getattr(path, "is_junction", lambda: False)()


def remove_link(path):
    if path.is_symlink():
        path.unlink()
    else:
        os.rmdir(path)  # a junction: removes the link, not the target


def make_link(link, target):
    # Windows symlinks need Developer Mode or admin; a directory junction needs neither.
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        if os.name != "nt":
            raise
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], check=True, capture_output=True)


# One root for everything the harness owns
(here / "feedback").mkdir(exist_ok=True)
if install:
    for name in ("config", "cache", "state", "workspaces", "logs"):
        (gp_home / name).mkdir(parents=True, exist_ok=True)
for name, target in (("harness", here / "harness"), ("feedback", here / "feedback")):
    root_link = gp_home / name
    if is_link(root_link):
        remove_link(root_link)
    if install:
        if root_link.exists():
            sys.exit(f"install.sh: {root_link} exists and is not a link; move it away first")
        make_link(root_link, target)
        print(f"linked {root_link} -> {target}")
# Legacy top-level links from before the single root: remove them, never anything that is not a link
for old in (".harness", ".harness-feedback"):
    if is_link(home / old):
        remove_link(home / old)
        print(f"removed legacy link {home / old}")
if not install:
    try:
        gp_home.rmdir()  # only when no runtime state is left
    except OSError:
        pass

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
                    if not any(m in h.get("command", "") for h in g.get("hooks", []) for m in HOOK_MARKS)]
if install:
    hook = lambda name: {"type": "command", "command": f'"{gp_home}/harness/hooks/{name}"'}
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
    print(f"removed allow rule {a} (CLD.1: use ~/.golden-path-harness/harness/tools/cloud/cloud-read.sh)")

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

# /tv-review for Claude Code; /example was dropped, so remove any copy left by an older install
for name in ("example", "tv-review"):
    skill = home / ".claude" / "skills" / name / "SKILL.md"
    if install and name == "tv-review":
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
    for f in ((example,) if install else (instructions, example)):
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
