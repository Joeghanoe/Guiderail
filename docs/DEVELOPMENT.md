# Adding to the plugin

This document is the entry point for engineers contributing skills, agents, hooks, MCP servers, or instructions to the TeamValue AI Hub plugin.

## Rules that apply to everything

- **Kebab-case names everywhere.** Plugin `name`, skill `name`, agent `name`, MCP server keys. Lowercase letters, digits, hyphens. No slashes. No colons. No uppercase. No underscores.
- **The `name:` in frontmatter MUST match the leaf folder name** for skills. Mismatch = silent load failure.
- **Bump versions in lockstep.** `plugin.json` and `.github/plugin/marketplace.json` both carry `version` — bump them together.

## Add a new skill

1. Pick a category — `bicep`, `frontend`, etc. Reuse if it fits.
2. Create the folder structure:
   - Top-level skill: `skills/<name>/SKILL.md`
   - Nested under a category: `skills/<category>/<name>/SKILL.md`. The leaf folder name must be unique across all skills (PluginPlan §10) — disambiguate with a prefix if needed (e.g. `skills/frontend/frontend-security`).
3. `SKILL.md` frontmatter:
   ```markdown
   ---
   name: my-skill-name
   description: One precise sentence used by the agent to decide whether to load this skill. Keep it keyword-rich.
   ---

   # My Skill Title

   ## When to use
   ...

   ## Resources
   - [reference doc](./references/foo.md)

   ## Rules
   1. ...
   ```
4. Place supporting documents under `skills/<name>/references/`. Keep individual reference files focused — large files degrade response quality.
5. Add the skill path to the manifest:
   - `plugin.json` → `skills` array

## Add a new agent

1. Pick a category folder under `agents/` (`architecture`, `backend`, …) or add a new one.
2. File: `agents/<category>/<name>.agent.md`. The `<name>` must be kebab-case.
3. Frontmatter:
   ```markdown
   ---
   name: agent-name
   description: One sentence describing the agent's persona and when to invoke.
   tools: [search/codebase, read/readFile, ...]   # optional — Copilot tool IDs
   ---
   ```
4. If you add a new category folder, add it to the `agents` array in the manifest.

## Add a hook

`hooks.json` currently ships empty. To wire up lifecycle automation:

```json
{
  "PreToolUse": [
    {
      "matcher": "Edit|Write",
      "command": "pwsh -NoProfile -File hooks/check-secrets.ps1"
    }
  ]
}
```

- Place hook scripts under `hooks/` (create the folder).
- Hook scripts must exit `0` to allow, non-zero to block.

Document each hook in `docs/HOOKS.md` (create when the first hook lands) — engineers need to understand which guardrails are active before they install.

## Add an MCP server

`.mcp.json` currently ships empty. Pattern:

```json
{
  "mcpServers": {
    "teamvalue-context": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "${TEAMVALUE_PRINCIPLES_PATH}"]
    }
  }
}
```

The `teamvalue-context` server is per-engineer-machine-specific — the principles folder is at a different absolute path for each engineer. Don't hardcode an absolute path; either:
- Use a documented environment variable (`$env:TEAMVALUE_PRINCIPLES_PATH`), set during onboarding, or
- Extend `install.ps1` to prompt for the path at install time and write the resolved value locally (leave the repo `.mcp.json` template generic).

## Updating instructions

Top-level instructions live in `instructions/`:
- `global.instructions.md` — applies in every conversation
- `principles.instructions.md` — TeamValue principle reference
- `security.instructions.md` — security defaults

These live in `instructions/` and are loaded automatically by GitHub Copilot via the plugin manifest. Edits propagate without reinstall.

## Version bump checklist

When releasing a change:

- [ ] Bump `version` in `plugin.json`
- [ ] Bump `metadata.version` and `plugins[0].version` in `.github/plugin/marketplace.json`
- [ ] Run `pwsh ./scripts/validate.ps1` (once written — see verification section of the plan)
- [ ] Update `README.md` if user-facing behaviour changed
- [ ] Tag the commit: `git tag v1.x.x && git push --tags`

## Validation (manual until CI lands)

```powershell
# kebab-case checks
$p = Get-Content plugin.json | ConvertFrom-Json
if ($p.name -notmatch '^[a-z0-9-]+$') { throw "plugin name not kebab-case" }

# skill name/folder agreement
Get-ChildItem skills -Recurse -Filter SKILL.md | ForEach-Object {
    $folder = $_.Directory.Name
    $name = (Get-Content $_.FullName -TotalCount 5 | Select-String '^name:').ToString() -replace '^name:\s*', ''
    if ($name -ne $folder) { Write-Warning "MISMATCH: $($_.FullName) — name='$name', folder='$folder'" }
}
```
