<#
.SYNOPSIS
    Install the TeamValue AI Hub plugin for GitHub Copilot.

.DESCRIPTION
    Registers this repo as a plugin marketplace in VS Code user settings
    (chat.plugins.marketplaces). Idempotent — re-running does not duplicate entries.

.PARAMETER Force
    Overwrite existing entries without prompting.

.EXAMPLE
    .\install.ps1
    .\install.ps1 -Force
#>

[CmdletBinding()]
param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$pluginRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Test-CopilotInstalled {
    Test-Path "$env:APPDATA\Code"
}

function Install-Copilot {
    param([string]$RepoRoot)

    if (-not (Test-CopilotInstalled)) {
        throw "VS Code not detected. Install VS Code before running this script."
    }

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
        Write-Host "  Added marketplace entry: $marketplaceEntry" -ForegroundColor Green
    } else {
        Write-Host "  Marketplace entry already present (idempotent skip)." -ForegroundColor Yellow
    }

    Write-Host "  Reload VS Code (Ctrl+Shift+P -> 'Reload Window')." -ForegroundColor Cyan
    Write-Host "  No popup will appear — agents and skills load automatically after reload." -ForegroundColor Cyan
    Write-Host "  Verify: open Copilot Chat and type '@' (agents) or '/' (skills)." -ForegroundColor Cyan
}





# Main
Write-Host "TeamValue AI Hub installer" -ForegroundColor Magenta
Write-Host "Repo: $pluginRoot"
Write-Host ""

Install-Copilot -RepoRoot $pluginRoot

Write-Host ""
Write-Host "Done." -ForegroundColor Green
