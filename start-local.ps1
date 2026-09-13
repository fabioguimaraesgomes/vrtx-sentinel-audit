$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$azuriteLocation = Join-Path $projectRoot '.azurite'
$azuriteDebugLog = Join-Path $azuriteLocation 'azurite-debug.log'

if (-not (Test-Path $azuriteLocation)) {
    New-Item -ItemType Directory -Path $azuriteLocation | Out-Null
}

Write-Host 'Starting Azurite on 127.0.0.1:10000, 10001, 10002...'
Start-Process -FilePath 'npx.cmd' -ArgumentList @(
    '-y',
    'azurite',
    '--silent',
    '--location', $azuriteLocation,
    '--debug', $azuriteDebugLog
) -WorkingDirectory $projectRoot | Out-Null

Write-Host 'Starting Azure Functions host...'
Set-Location $projectRoot
& '.\.venv\Scripts\Activate.ps1'
func start --no-bundles