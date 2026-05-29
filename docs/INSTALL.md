# Installation Guide

## Prerequisites

- **PowerShell 7+** (`pwsh`) — for the install script
- **Git** — to clone the repo
- **VS Code** with **GitHub Copilot Chat** extension, *or*
- **Claude Code** (CLI or IDE extension)

## One-command install

```powershell
git clone https://github.com/TeamValue/TeamValue.AiHub.GitHubCopilot.git
cd TeamValue.AiHub.GitHubCopilot
.\install.ps1
```

Flags:

| Flag | Effect |
|---|---|
| `-Target copilot` | Install only for VS Code Copilot |
| `-Target claude`  | Install only for Claude Code |
| `-Target both`    | Install for both (default when both are detected) |
| `-Force`          | Overwrite existing symlinks/copies without prompting |

The script is idempotent — re-running does not duplicate entries.

## What `install.ps1` does

### For GitHub Copilot (VS Code)

Appends the cloned repo path to `chat.plugins.marketplaces` in `%APPDATA%\Code\User\settings.json`.

> **No popup will appear.** After reloading the window (`Ctrl+Shift+P` → *Reload Window*), agents and skills load automatically. Verify by opening Copilot Chat and typing `@` (agents) or `/` (skills).

### For Claude Code

1. Symlinks every `agents/<category>/<name>.agent.md` → `~/.claude/agents/<name>.md` (drops the `.agent` segment because Claude expects flat `<name>.md`).
2. Symlinks every skill folder declared in `plugin.json` → `~/.claude/skills/<leaf-name>`.
3. Appends `@import <abs-path>/instructions/global.instructions.md` to `~/.claude/CLAUDE.md`, wrapped in marker comments so re-runs don't duplicate.
4. Merges any entries in `.mcp.json` into `~/.claude/.mcp.json` (currently empty — no merge happens).

If symlink creation fails (non-admin Windows shell without Developer Mode), the script falls back to copy. Copy mode means edits to the source repo do **not** auto-propagate — re-run `install.ps1` after pulling updates.

## Workspace-level recommendation

To recommend this plugin to every engineer opening a TeamValue project, add to the project's `.vscode/settings.json`:

```jsonc
{
  "chat.plugins.marketplaces": [
    "https://github.com/TeamValue/TeamValue.AiHub.GitHubCopilot.git"
  ]
}
```

> **No automatic popup.** VS Code will not pop up a notification. Each engineer must manually run **Chat: Install Plugin From Source** once (see steps above). After that, the agents and skills load automatically in every session.

## Manual install (without the script)

### Copilot — install from Git URL

1. Open VS Code.
2. Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`).
3. Run **Chat: Install Plugin From Source**.
4. Paste the URL: `https://github.com/TeamValue/TeamValue.AiHub.GitHubCopilot.git`
5. Press **Enter** and wait for VS Code to clone the plugin.
6. Run **Reload Window** (`Ctrl+Shift+P` → *Reload Window*).

> **No popup will appear** — this is expected. There is no confirmation dialog or notification after the install completes. After the window reloads, open Copilot Chat and type `@` to see agents or `/` to see skills.

### Claude Code — symlink by hand (PowerShell)

```powershell
$repo = "C:\path\to\TeamValue.AiHub.GitHubCopilot"
$claude = "$env:USERPROFILE\.claude"

# Agents — flatten and drop .agent segment
Get-ChildItem "$repo\agents" -Recurse -Filter *.agent.md | ForEach-Object {
    $name = $_.Name -replace '\.agent\.md$', '.md'
    New-Item -ItemType SymbolicLink -Path "$claude\agents\$name" -Value $_.FullName
}

# Skills — read paths from plugin.json
$plugin = Get-Content "$repo\plugin.json" | ConvertFrom-Json
foreach ($p in $plugin.skills) {
    $leaf = Split-Path -Leaf $p
    New-Item -ItemType SymbolicLink -Path "$claude\skills\$leaf" -Value (Join-Path $repo $p)
}
```

## Verifying the install

After install, in a fresh editor session:

- **Copilot**: Open Copilot Chat → `@` should show TeamValue agents; `/` should show skills.
- **Claude Code**: Run `claude --debug` (or open a new session); the agents and skills load from `~/.claude/agents` and `~/.claude/skills`.

## Updating

```powershell
git pull
.\install.ps1   # idempotent — refreshes any stale state
```

In symlink mode this is essentially a no-op (links already point at the new content). In copy fallback mode the script overwrites copies with updated source.

## Uninstall

```powershell
.\uninstall.ps1
```

See `README.md` → Uninstall section.
