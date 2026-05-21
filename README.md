# TeamValue AI Hub

A dual-target plugin packaging TeamValue's agents, skills, hooks, and MCP servers for **GitHub Copilot** (VS Code) and **Claude Code**. One repo, two installations, the same content.

## What's in the box

| Component | Status | Notes |
|---|---|---|
| Agents | scaffolded | `arie-architecture`, `barry-backend`, `dirk-devops`, `donald-docs`, `freddy-frontend`, `henk`, `irene-infra`, `ria-review`, `thomas-test` |
| Skills | scaffolded | `architecture`, `bicep`, `devops`, `dotnet`, `frontend/{architecture,security,state-data}`, `powershell`, `typescript` |
| Instructions | partial | `global`, `principles` (54 lines), `security` (skeleton) |
| Hooks | empty | `hooks.json` — `PreToolUse`/`PostToolUse`/`Stop` arrays present, no entries |
| MCP servers | empty | `.mcp.json` — `mcpServers` object present, no entries |

Most agent and skill bodies are intentionally empty in this release. The focus is plumbing — manifests, installer, marketplace registration — so engineers can plug in and we fill content incrementally without breaking distribution.

## Install

### One-command install (recommended)

```powershell
git clone https://github.com/TeamValue/TeamValue.AiHub.GitHubCopilot.git
cd TeamValue.AiHub.GitHubCopilot
.\install.ps1
```

The script auto-detects VS Code and Claude Code, asks which target(s) you want, and wires up both sides idempotently. Re-run any time to refresh.

### Manual (GitHub Copilot — VS Code)

1. Command Palette → **Chat: Install Plugin From Source**
2. Enter the repo URL.
3. Reload VS Code.

### Manual (Claude Code)

1. Symlink or copy `agents/<category>/<name>.agent.md` to `~/.claude/agents/<name>.md` (drop the `.agent` segment).
2. Symlink each skill folder listed in `plugin.json` to `~/.claude/skills/`.
3. Add `@import <repo>/instructions/global.instructions.md` to `~/.claude/CLAUDE.md`.

`install.ps1` does all of the above for you.

## Uninstall

```powershell
.\uninstall.ps1
```

Removes Claude symlinks and CLAUDE.md import. For Copilot, it strips the marketplace entry from VS Code settings; installed plugin instances must be removed via the VS Code Extensions UI.

## Adding skills, agents, hooks

See [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).

## Cross-tool differences

See [`docs/DUAL_TARGET.md`](docs/DUAL_TARGET.md) for the file-format and behaviour differences between Copilot and Claude Code.

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Plugin does not appear after install | `chat.plugins.enabled` is `false` in VS Code | Ask the workspace admin to enable it |
| Skill silently fails to load | `name:` in `SKILL.md` frontmatter doesn't match the leaf folder name | Make them identical (kebab-case) |
| Symlink creation fails on Windows | Non-admin shell with developer mode off | Either enable Windows Developer Mode, run PowerShell as admin, or re-run `install.ps1` (it falls back to copy) |
| Claude doesn't see the agent | File still named `*.agent.md` in `~/.claude/agents/` | Claude expects `<name>.md` (no `.agent`); re-run install.ps1 |

## License

MIT.
