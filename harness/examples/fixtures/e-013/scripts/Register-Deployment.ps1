param(
    [string]$ResourceGroup,
    [string]$Name,
    [int]$TimeoutMinutes = 15
)

$deadline = (Get-Date).AddMinutes($TimeoutMinutes)
do {
    $state = az deployment group show -g $ResourceGroup -n $Name `
        --query properties.provisioningState -o tsv
    if ($state -eq 'Succeeded') {
        break
    }
    Start-Sleep -Seconds 20
} while ((Get-Date) -lt $deadline)

if ($state -ne 'Succeeded') {
    throw "Deployment is $state"
}
