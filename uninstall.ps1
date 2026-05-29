<#
.SYNOPSIS
    Uninstall the TeamValue AI Hub plugin from GitHub Copilot.

.DESCRIPTION
    Removes the marketplace entry from VS Code user settings
    (chat.plugins.marketplaces). Idempotent — safe to re-run.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$pluginRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

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
            Write-Host "  Removed marketplace entry: $marketplaceEntry" -ForegroundColor Green
            Write-Host "  Note: any installed plugin instances must be removed via VS Code UI." -ForegroundColor Yellow
        } else {
            Write-Host "  Marketplace entry not present." -ForegroundColor Yellow
        }
    }
}

Write-Host "TeamValue AI Hub uninstaller" -ForegroundColor Magenta
Write-Host ""
Uninstall-Copilot -RepoRoot $pluginRoot
Write-Host ""
Write-Host "Done." -ForegroundColor Green
