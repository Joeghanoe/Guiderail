# Dual-target compatibility (Copilot ↔ Claude Code)

This plugin ships one repo that two different agent tools consume. The file formats are similar but not identical. This page lists every divergence and how `install.ps1` reconciles it.

## Side-by-side

| Concern | GitHub Copilot (VS Code) | Claude Code |
|---|---|---|
| Plugin manifest | `plugin.json` at repo root | `.claude-plugin/plugin.json` |
| Marketplace registry | `.github/plugin/marketplace.json` | Not used (Claude reads manifests directly) |
| Settings registration | `chat.plugins.marketplaces` in `%APPDATA%\Code\User\settings.json` | Plugin path under `~/.claude/` |
| Skill folder | `skills/<name>/SKILL.md` | `skills/<name>/SKILL.md` ✅ identical |
| Skill frontmatter `name` | Must equal folder name (kebab-case) | Must equal folder name (kebab-case) ✅ identical |
| Agent file | `agents/<name>.agent.md` (or nested `agents/<category>/<name>.agent.md`) | `~/.claude/agents/<name>.md` — flat, no `.agent` segment |
| Agent frontmatter `name` | Kebab-case | Kebab-case ✅ identical |
| Agent `tools` array | Copilot tool IDs (`search/codebase`, `edit/editFiles`, …) | Claude tool names (`Read`, `Edit`, `Bash`, …) |
| Hooks | `hooks.json` — `PreToolUse`/`PostToolUse`/… arrays | `hooks.json` — same shape |
| MCP servers | `.mcp.json` — `mcpServers` map | `.mcp.json` (merged into `~/.claude/.mcp.json`) |
| Lifecycle event names | `PreToolUse`, `PostToolUse`, … | Same names — semantics may differ slightly per tool |

## Where `install.ps1` papers over differences

### Agent filename

Source files are `agents/<category>/<name>.agent.md`. For Claude, `install.ps1` creates a symlink `~/.claude/agents/<name>.md` (drops the `.agent` segment and flattens the category). For Copilot, no rewrite needed — the plugin loader handles `*.agent.md` natively.

### CLAUDE.md import

Copilot reads instructions via the plugin manifest. Claude reads them via `@import` lines in `~/.claude/CLAUDE.md`. `install.ps1` appends an `@import` block bracketed by marker comments so re-runs and uninstalls are idempotent.

### MCP path templating

The `teamvalue-context` filesystem MCP needs an absolute path to the principles directory, which varies per engineer. The repo's `.mcp.json` should ship with `${TEAMVALUE_PRINCIPLES_PATH}` (or similar) and `install.ps1` should prompt for and write the resolved value into `~/.claude/.mcp.json` only — never into the committed `.mcp.json`.

(Not implemented yet — `.mcp.json` ships empty.)

### Tool name divergence in agent frontmatter

The existing `arie-architecture` agent declares Copilot-format tools (`microsoft.docs.mcp`, `azure_query_learn`, …). Claude will silently ignore tool names it doesn't recognise. **Decision deferred:** either (a) maintain two tool lists with a build step that picks per target, or (b) accept that unknown tools are no-ops and let each tool ignore what it doesn't understand. Today we ship (b).

## What is *not* dual-target

- VS Code-specific tool IDs (`vscodeAPI`, `runTasks`, `openSimpleBrowser`) have no Claude analogue.
- Claude Code skills with progressive disclosure / `argument-hint` work in Claude but Copilot may ignore those fields.

Document anything new that needs translation here as you add it.
