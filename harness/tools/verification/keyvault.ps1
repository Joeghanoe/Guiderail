param(
    [Parameter(Mandatory)][string]$ToolsDirectory,
    [Parameter(Mandatory)][string]$TemplateFile,
    [string]$ParameterFile,
    [Parameter(Mandatory)][string]$OutputFile
)
$ErrorActionPreference = 'Stop'
try {
    $lock = Get-Content -Raw (Join-Path $PSScriptRoot 'tool-lock.json') | ConvertFrom-Json
    foreach ($module in @('PSRule', 'PSRule.Rules.Azure')) {
        $version = $lock.modules.$module.version
        Import-Module (Join-Path $ToolsDirectory "modules/$module/$version/$module.psd1") -ErrorAction Stop
        if ((Get-Module $module).Version.ToString() -ne $version) { throw "Unexpected $module version" }
    }
    $arguments = @{TemplateFile = $TemplateFile; PassThru = $true}
    if ($ParameterFile) { $arguments.ParameterFile = $ParameterFile }
    $vaults = @(Export-AzRuleTemplateData @arguments | Where-Object { $_.type -eq 'Microsoft.KeyVault/vaults' })
    $rules = @($lock.keyvault_rules)
    $results = @()
    if ($vaults.Count -gt 0) {
        $results = @($vaults | Invoke-PSRule -Module PSRule.Rules.Azure -Name $rules -Outcome All |
            ForEach-Object { [pscustomobject]@{rule = $_.RuleName; target = $_.TargetName; outcome = $_.Outcome.ToString()} })
        if ($results.Count -ne ($vaults.Count * $rules.Count)) { throw 'Incomplete Key Vault policy coverage' }
        if (@($results | Where-Object { $_.outcome -notin @('Pass','Fail') }).Count -gt 0) { throw 'Unprocessed or errored Key Vault rule' }
    }
    @{schema_version = 1; vaults = $vaults.Count; rules = $rules; results = $results} |
        ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 $OutputFile
    if (@($results | Where-Object outcome -eq 'Fail').Count -gt 0) { exit 1 }
    exit 0
}
catch {
    Write-Error $_ -ErrorAction Continue
    exit 2
}
