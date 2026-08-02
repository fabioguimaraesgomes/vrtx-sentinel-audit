# start-local.ps1 - reproducible local startup
Set-Location "$PSScriptRoot"
# Activate venv if exists (.venv preferred, fallback to .venv-1)
if (Test-Path .\.venv\Scripts\Activate.ps1) {
  & .\.venv\Scripts\Activate.ps1
} elseif (Test-Path .\.venv-1\Scripts\Activate.ps1) {
  & .\.venv-1\Scripts\Activate.ps1
}
# Start Azurite if installed locally (try to start if azurite command exists)
if (Get-Command azurite -ErrorAction SilentlyContinue) {
  Start-Process -NoNewWindow -FilePath azurite
} else {
  Write-Output 'Azurite not found; skip. Use Azurite for Storage emulation if needed.'
}

# Resolve Functions project root automatically.
$hostFile = Get-ChildItem -Path . -Recurse -File -Filter host.json -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $hostFile) {
  Write-Error 'No host.json found. Cannot start Azure Functions from this repository root.'
  exit 1
}

$funcRoot = Split-Path -Parent $hostFile.FullName
Set-Location $funcRoot
Write-Output "Functions root detected: $funcRoot"

# Start Functions Core Tools without extension bundles to avoid downloads
func start --no-bundles
