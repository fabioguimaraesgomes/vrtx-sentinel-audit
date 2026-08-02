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
# Start Functions Core Tools without extension bundles to avoid downloads
func start --no-bundles
