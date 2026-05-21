<#
.SYNOPSIS
    Uninstall the TeamValue AI Hub plugin from GitHub Copilot and/or Claude Code.

.DESCRIPTION
    Removes symlinks created by install.ps1, strips the marker-bracketed @import
    block from ~/.claude/CLAUDE.md, and comments out (does not delete) the
    marketplace entry in VS Code settings to avoid silently mutating user config.

.PARAMETER Target
    Restrict uninstallation to 'copilot', 'claude', or 'both' (default).
#>

[CmdletBinding()]
param(
    [ValidateSet('copilot', 'claude', 'both')]
    [string]$Target = 'both'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$pluginRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$marker = "# TeamValue AI Hub (managed by install.ps1)"

function Uninstall-Copilot {
    param([string]$RepoRoot)

    $settingsPath = "$env:APPDATA\Code\User\settings.json"
    if (-not (Test-Path $settingsPath)) {
        Write-Host "  [Copilot] No settings.json found, nothing to uninstall." -ForegroundColor Yellow
        return
    }

    $marketplaceEntry = (Resolve-Path $RepoRoot).Path -replace '\\', '/'
    $raw = Get-Content -Raw -Path $settingsPath
    $settings = $raw | ConvertFrom-Json

    $hasProp = $settings.PSObject.Properties.Name -contains 'chat.plugins.marketplaces'
    if ($hasProp) {
        $current = @($settings.'chat.plugins.marketplaces')
        $filtered = $current | Where-Object { $_ -ne $marketplaceEntry }
        if (@($filtered).Count -lt $current.Count) {
            $settings.'chat.plugins.marketplaces' = @($filtered)
            $settings | ConvertTo-Json -Depth 10 | Set-Content -Path $settingsPath -Encoding UTF8
            Write-Host "  [Copilot] Removed marketplace entry: $marketplaceEntry" -ForegroundColor Green
            Write-Host "  [Copilot] Note: any installed plugin instances must be removed via VS Code UI." -ForegroundColor Yellow
        } else {
            Write-Host "  [Copilot] Marketplace entry not present." -ForegroundColor Yellow
        }
    }
}

function Uninstall-Claude {
    param([string]$RepoRoot)

    $claudeRoot = "$env:USERPROFILE\.claude"

    # Remove agent symlinks
    if (Test-Path "$claudeRoot\agents") {
        Get-ChildItem -Path "$RepoRoot\agents" -Recurse | Where-Object { $_.Name -like '*.agent.md' } | ForEach-Object {
            $linkName = $_.Name -replace '\.agent\.md$', '.md'
            $linkPath = "$claudeRoot\agents\$linkName"
            if (Test-Path $linkPath) {
                Remove-Item -Path $linkPath -Force
                Write-Host "    removed: $linkPath" -ForegroundColor Green
            }
        }
    }

    # Remove skill symlinks — mirror install.ps1 stem-based logic.
    if (Test-Path "$claudeRoot\skills") {
        $pluginJson = Get-Content -Raw -Path "$RepoRoot\plugin.json" | ConvertFrom-Json
        foreach ($skillPath in $pluginJson.skills) {
            $skillSource = Join-Path $RepoRoot $skillPath
            Get-ChildItem -Path $skillSource -Filter '*.skill.md' | ForEach-Object {
                $stem = $_.BaseName -replace '\.skill$', ''
                $linkPath = "$claudeRoot\skills\$stem"
                if (Test-Path $linkPath) {
                    Remove-Item -Path $linkPath -Recurse -Force
                    Write-Host "    removed: $linkPath" -ForegroundColor Green
                }
            }
        }
    }

    # Strip CLAUDE.md import block
    $claudeMd = "$claudeRoot\CLAUDE.md"
    if (Test-Path $claudeMd) {
        $content = Get-Content -Raw -Path $claudeMd
        $pattern = "(?ms)\r?\n?$([regex]::Escape($marker)).*?# end TeamValue AI Hub\r?\n?"
        $stripped = [regex]::Replace($content, $pattern, '')
        if ($stripped -ne $content) {
            $stripped | Set-Content -Path $claudeMd -Encoding UTF8 -NoNewline
            Write-Host "  [Claude] Removed @import block from CLAUDE.md" -ForegroundColor Green
        }
    }
}

Write-Host "TeamValue AI Hub uninstaller" -ForegroundColor Magenta

$targets = if ($Target -eq 'both') { @('copilot', 'claude') } else { @($Target) }

foreach ($t in $targets) {
    Write-Host ""
    Write-Host "Uninstalling for: $t" -ForegroundColor Magenta
    switch ($t) {
        'copilot' { Uninstall-Copilot -RepoRoot $pluginRoot }
        'claude'  { Uninstall-Claude  -RepoRoot $pluginRoot }
    }
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
