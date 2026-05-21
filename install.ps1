<#
.SYNOPSIS
    Install the TeamValue AI Hub plugin for GitHub Copilot and/or Claude Code.

.DESCRIPTION
    Detects which targets are installed, prompts the user, then wires the plugin
    into each tool. Idempotent — re-running does not duplicate entries.

    For GitHub Copilot: registers this repo as a plugin marketplace in VS Code
    user settings (chat.plugins.marketplaces).

    For Claude Code: symlinks (or copies on non-admin) every agent and skill
    into ~/.claude/agents and ~/.claude/skills, appends an @import for
    instructions/global.instructions.md to ~/.claude/CLAUDE.md, and merges
    .mcp.json into ~/.claude/.mcp.json.

.PARAMETER Target
    Restrict installation to a single target: 'copilot', 'claude', or 'both'
    (default). Skips the interactive prompt when supplied.

.PARAMETER Force
    Overwrite existing symlinks/files without prompting.

.EXAMPLE
    .\install.ps1
    .\install.ps1 -Target claude
    .\install.ps1 -Target both -Force
#>

[CmdletBinding()]
param(
    [ValidateSet('copilot', 'claude', 'both')]
    [string]$Target,

    [switch]$Force
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$pluginRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pluginName = 'teamvalue-aihub'
$marker = "# TeamValue AI Hub (managed by install.ps1)"

function Test-CopilotInstalled {
    Test-Path "$env:APPDATA\Code"
}

function Test-ClaudeInstalled {
    Test-Path "$env:USERPROFILE\.claude"
}

function Get-Targets {
    param([string]$Requested)

    if ($Requested) {
        if ($Requested -eq 'both') { return @('copilot', 'claude') }
        return @($Requested)
    }

    $copilotPresent = Test-CopilotInstalled
    $claudePresent = Test-ClaudeInstalled

    if (-not $copilotPresent -and -not $claudePresent) {
        throw "Neither VS Code nor Claude Code detected. Install at least one before running this script."
    }

    Write-Host ""
    Write-Host "Detected targets:" -ForegroundColor Cyan
    Write-Host "  VS Code (Copilot): $(if ($copilotPresent) { 'yes' } else { 'no' })"
    Write-Host "  Claude Code:       $(if ($claudePresent) { 'yes' } else { 'no' })"
    Write-Host ""

    $available = @()
    if ($copilotPresent) { $available += 'copilot' }
    if ($claudePresent) { $available += 'claude' }

    if ($available.Count -eq 1) {
        return $available
    }

    $choice = Read-Host "Install for [b]oth, [c]opilot only, or c[l]aude only? (default: both)"
    switch -Regex ($choice) {
        '^c$|^copilot' { return @('copilot') }
        '^l$|^claude'  { return @('claude') }
        default        { return @('copilot', 'claude') }
    }
}

function Install-Copilot {
    param([string]$RepoRoot)

    $settingsPath = "$env:APPDATA\Code\User\settings.json"

    if (-not (Test-Path $settingsPath)) {
        New-Item -ItemType Directory -Force -Path (Split-Path $settingsPath) | Out-Null
        '{}' | Set-Content -Path $settingsPath -Encoding UTF8
    }

    $raw = Get-Content -Raw -Path $settingsPath
    $settings = if ([string]::IsNullOrWhiteSpace($raw)) { New-Object PSObject } else { $raw | ConvertFrom-Json }

    $marketplaceEntry = (Resolve-Path $RepoRoot).Path -replace '\\', '/'

    $existing = if ($settings.PSObject.Properties.Name -contains 'chat.plugins.marketplaces') {
        @($settings.'chat.plugins.marketplaces')
    } else {
        @()
    }

    if ($existing -notcontains $marketplaceEntry) {
        $newList = $existing + $marketplaceEntry
        if ($settings.PSObject.Properties.Name -contains 'chat.plugins.marketplaces') {
            $settings.'chat.plugins.marketplaces' = $newList
        } else {
            $settings | Add-Member -NotePropertyName 'chat.plugins.marketplaces' -NotePropertyValue $newList
        }
        $settings | ConvertTo-Json -Depth 10 | Set-Content -Path $settingsPath -Encoding UTF8
        Write-Host "  [Copilot] Added marketplace entry: $marketplaceEntry" -ForegroundColor Green
    } else {
        Write-Host "  [Copilot] Marketplace entry already present (idempotent skip)." -ForegroundColor Yellow
    }

    Write-Host "  [Copilot] Reload VS Code, then accept the plugin recommendation prompt." -ForegroundColor Cyan
}

function New-PluginSymlink {
    param([string]$Source, [string]$Target)

    if (Test-Path $Target) {
        if (-not $Force) {
            Write-Host "    skip (exists): $Target" -ForegroundColor Yellow
            return
        }
        Remove-Item -Path $Target -Recurse -Force
    }

    $parent = Split-Path $Target
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }

    try {
        New-Item -ItemType SymbolicLink -Path $Target -Value $Source -ErrorAction Stop | Out-Null
        Write-Host "    link: $Target -> $Source" -ForegroundColor Green
    } catch {
        Copy-Item -Path $Source -Destination $Target -Recurse -Force
        Write-Host "    copy: $Target (symlink failed, fell back to copy)" -ForegroundColor Yellow
    }
}

function Install-Claude {
    param([string]$RepoRoot)

    $claudeRoot = "$env:USERPROFILE\.claude"
    $agentsDest = "$claudeRoot\agents"
    $skillsDest = "$claudeRoot\skills"

    New-Item -ItemType Directory -Force -Path $agentsDest, $skillsDest | Out-Null

    # Agents — flatten category folders, drop .agent segment.
    Write-Host "  [Claude] Linking agents..."
    Get-ChildItem -Path "$RepoRoot\agents" -Recurse | Where-Object { $_.Name -like '*.agent.md' } | ForEach-Object {
        $newName = $_.Name -replace '\.agent\.md$', '.md'
        New-PluginSymlink -Source $_.FullName -Target "$agentsDest\$newName"
    }

    # Skills — for each declared folder, create a per-.skill.md subfolder with a SKILL.md symlink.
    # Claude Code expects ~/.claude/skills/<name>/SKILL.md; repo keeps original descriptive filenames.
    Write-Host "  [Claude] Linking skills..."
    $pluginJson = Get-Content -Raw -Path "$RepoRoot\plugin.json" | ConvertFrom-Json
    foreach ($skillPath in $pluginJson.skills) {
        $skillSource = Join-Path $RepoRoot $skillPath
        $skillFiles = Get-ChildItem -Path $skillSource -Filter '*.skill.md'
        foreach ($sf in $skillFiles) {
            $stem = $sf.BaseName -replace '\.skill$', ''
            $destFolder = "$skillsDest\$stem"
            if (-not (Test-Path $destFolder)) {
                New-Item -ItemType Directory -Force -Path $destFolder | Out-Null
            }
            New-PluginSymlink -Source $sf.FullName -Target "$destFolder\SKILL.md"
        }
    }

    # CLAUDE.md import — idempotent via marker comment.
    $claudeMd = "$claudeRoot\CLAUDE.md"
    if (-not (Test-Path $claudeMd)) {
        '' | Set-Content -Path $claudeMd -Encoding UTF8
    }

    $globalInstructions = (Resolve-Path "$RepoRoot\instructions\global.instructions.md").Path
    $importLine = "@import $globalInstructions"
    $block = @"

$marker
$importLine
# end TeamValue AI Hub
"@

    $existing = Get-Content -Raw -Path $claudeMd
    if ($existing -notmatch [regex]::Escape($marker)) {
        Add-Content -Path $claudeMd -Value $block -Encoding UTF8
        Write-Host "  [Claude] Added @import for global instructions to CLAUDE.md" -ForegroundColor Green
    } else {
        Write-Host "  [Claude] CLAUDE.md import already present (idempotent skip)." -ForegroundColor Yellow
    }

    # .mcp.json merge — skip while plugin .mcp.json is empty.
    $pluginMcp = "$RepoRoot\.mcp.json"
    $userMcp = "$claudeRoot\.mcp.json"
    if (Test-Path $pluginMcp) {
        $mcp = Get-Content -Raw -Path $pluginMcp | ConvertFrom-Json
        if ($mcp.mcpServers -and @($mcp.mcpServers.PSObject.Properties).Count -gt 0) {
            Write-Host "  [Claude] Merging MCP servers..."
            $user = if (Test-Path $userMcp) { Get-Content -Raw -Path $userMcp | ConvertFrom-Json } else { [pscustomobject]@{ mcpServers = [pscustomobject]@{} } }
            foreach ($prop in $mcp.mcpServers.PSObject.Properties) {
                if ($user.mcpServers.PSObject.Properties.Name -contains $prop.Name) {
                    Write-Host "    skip (already defined): $($prop.Name)" -ForegroundColor Yellow
                } else {
                    $user.mcpServers | Add-Member -NotePropertyName $prop.Name -NotePropertyValue $prop.Value -Force
                    Write-Host "    add: $($prop.Name)" -ForegroundColor Green
                }
            }
            $user | ConvertTo-Json -Depth 10 | Set-Content -Path $userMcp -Encoding UTF8
        }
    }
}

# Main
Write-Host "TeamValue AI Hub installer" -ForegroundColor Magenta
Write-Host "Repo: $pluginRoot"

$targets = Get-Targets -Requested $Target

foreach ($t in $targets) {
    Write-Host ""
    Write-Host "Installing for: $t" -ForegroundColor Magenta
    switch ($t) {
        'copilot' { Install-Copilot -RepoRoot $pluginRoot }
        'claude'  { Install-Claude  -RepoRoot $pluginRoot }
    }
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
