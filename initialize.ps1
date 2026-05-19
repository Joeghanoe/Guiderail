# This script initializes the prompts by copying them from the "agents" and "skills" folders to the user's Code prompts directory. It should be run from the root of the repository.
$root = Get-Location
$sources = @(
  Join-Path $root "agents"
  Join-Path $root "skills"
  )
$dest = "$env:APPDATA\Code\User\prompts"

New-Item -ItemType Directory -Force -Path $dest | Out-Null

$copied = 0

foreach ($source in $sources) {
  if (-not (Test-Path -Path $source -PathType Container)) {
    Write-Warning "Skipping missing folder: $source"
    continue
  }

  Get-ChildItem -Path $source -Recurse -File | ForEach-Object {
    # Flatten all files into a single destination folder.
    Copy-Item -Path $_.FullName -Destination $dest -Force
    $copied++
  }
}

Write-Host "Done. $copied files copied to: $dest"