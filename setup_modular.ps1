# 1) Variables
$root = Get-Location
$services = @("security","automation","deception","identity","integration")
$libs = "libs"
$mocks = "mocks"
$release = "release"
$vscodeDir = ".vscode"

# 2) Git branch para trabajar sin romper main
git rev-parse --abbrev-ref HEAD 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
  git checkout -B refactor/modular
}

# 3) Crear estructura modular
foreach ($s in $services) { New-Item -ItemType Directory -Path (Join-Path $root "services\$s") -Force | Out-Null }
New-Item -ItemType Directory -Path (Join-Path $root $libs) -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $root $mocks) -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $root $release) -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $root $vscodeDir) -Force | Out-Null

# 4) Move existing function folders into modules (best-effort; adjust names if different)
# Mapping: extract_telemetry -> security, run_inference -> automation, publish_event -> automation, copilot_adapter -> integration
$map = @{
  "extract_telemetry" = "security"
  "run_inference" = "automation"
  "publish_event" = "automation"
  "copilot_adapter" = "integration"
}
foreach ($k in $map.Keys) {
  $src = Join-Path $root $k
  $dst = Join-Path $root ("services\" + $map[$k] + "\" + $k)
  if (Test-Path $src) {
    Move-Item -Path $src -Destination $dst -Force
  } else {
    # if not found, create placeholder folder so structure is explicit
    New-Item -ItemType Directory -Path $dst -Force | Out-Null
  }
}

# 5) Create local.settings.json.example with feature flags and placeholders (no secrets)
$localExample = @{
  IsEncrypted = $false
  Values = @{
    FUNCTIONS_WORKER_RUNTIME = "python"
    ENABLE_SECURITY = "true"
    ENABLE_AUTOMATION = "true"
    ENABLE_DECEPTION = "false"
    ENABLE_LLM = "false"
    AZURE_OPENAI_ENDPOINT = "<AZURE_OPENAI_ENDPOINT_PLACEHOLDER>"
    AZURE_OPENAI_KEY = "<KEY_IN_KEYVAULT_PLACEHOLDER>"
    ADX_CLUSTER = "<ADX_CLUSTER_PLACEHOLDER>"
    ADX_DATABASE = "<ADX_DATABASE_PLACEHOLDER>"
  }
}
$localExamplePath = Join-Path $root "local.settings.json.example"
$localExample | ConvertTo-Json -Depth 5 | Out-File -FilePath $localExamplePath -Encoding utf8

# 6) Ensure local.settings.json is ignored in git
$gitignore = Join-Path $root ".gitignore"
if (-not (Test-Path $gitignore)) { New-Item -ItemType File -Path $gitignore -Force | Out-Null }
$ignoreText = @(
  "local.settings.json",
  ".venv/",
  "__pycache__/",
  "*.pyc"
)
foreach ($line in $ignoreText) {
  if (-not (Select-String -Path $gitignore -Pattern ([regex]::Escape($line)) -Quiet)) {
    Add-Content -Path $gitignore -Value $line
  }
}

# 7) Create simple mocks for external services (OpenAI and ADX) to avoid credits
$openaiMock = @"
# mocks/openai_stub.py
def generate_response(prompt):
    # Stubbed response to avoid external calls in dev
    return {
        'text': '<<STUBBED LLM RESPONSE - enable real LLM with ENABLE_LLM=true and KeyVault secrets>>',
        'metadata': {'stub': True}
    }
"@
$adxMock = @"
# mocks/adx_stub.py
import json
_storage_file = 'mock_adx_storage.json'
def insert(record):
    try:
        with open(_storage_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\\n')
        return True
    except Exception as e:
        return False
"@
$openaiMockPath = Join-Path $root "mocks\openai_stub.py"
$adxMockPath = Join-Path $root "mocks\adx_stub.py"
$openaiMock | Out-File -FilePath $openaiMockPath -Encoding utf8 -Force
$adxMock | Out-File -FilePath $adxMockPath -Encoding utf8 -Force

# 8) Create start-local.ps1 to activate venv, start Azurite (if present) and start Functions without bundles
$startScript = @"
# start-local.ps1 - reproducible local startup
Set-Location `"$PSScriptRoot`"
# Activate venv if exists
if (Test-Path .\.venv\Scripts\Activate.ps1) {
    & .\.venv\Scripts\Activate.ps1
}
# Start Azurite if installed locally (try to start if azurite command exists)
if (Get-Command azurite -ErrorAction SilentlyContinue) {
    Start-Process -NoNewWindow -FilePath azurite
} else {
    Write-Output 'Azurite not found; skip. Use Azurite for Storage emulation if needed.'
}
# Start Functions Core Tools without extension bundles to avoid downloads
func start --no-bundles
"@
$startScriptPath = Join-Path $root "start-local.ps1"
$startScript | Out-File -FilePath $startScriptPath -Encoding utf8 -Force

# 9) Create .vscode/tasks.json to run the start script with one click
$tasksJson = @{
  version = "2.0.0"
  tasks = @(
    @{
      label = "Start VRTX Sentinel Local"
      type = "shell"
      command = "powershell -ExecutionPolicy Bypass -File `"$workspaceFolder\start-local.ps1`""
      problemMatcher = @()
      presentation = @{
        reveal = "always"
        panel = "shared"
      }
    }
  )
}
$tasksJsonPath = Join-Path $root ".vscode\tasks.json"
$tasksJson | ConvertTo-Json -Depth 6 | Out-File -FilePath $tasksJsonPath -Encoding utf8 -Force

# 10) Create placeholder dossiers in Markdown ready for conversion to PDF locally
$securityMd = @"
# Dossier Security - VRTX Sentinel
Version: v1
Resumen ejecutivo:
- Propósito: Auditoría y protección autónoma.
- Módulos incluidos: detectan fallos, analizan logs, alertan, protegen identidades, zero-trust dinámico, deception (desactivado por defecto).
Runbook de arranque local:
1. Copiar local.settings.json.example -> local.settings.json y rellenar placeholders con secretos en Key Vault.
2. Ejecutar .\start-local.ps1
3. Probar endpoint: http://localhost:7071/api/extract_telemetry
Anexos:
- Referencias a release/security-reports/
"@
$automationMd = @"
# Dossier Automation - VRTX Sentinel
Version: v1
Resumen ejecutivo:
- Propósito: Automatizar controles, orquestación y publicación de eventos.
- Módulos incluidos: reglas, playbooks, publish_event, integración Event Grid/ADX (stubs en dev).
Runbook de arranque local:
1. Copiar local.settings.json.example -> local.settings.json y activar ENABLE_AUTOMATION=true
2. Ejecutar .\start-local.ps1
3. Probar endpoint: http://localhost:7071/api/publish_event
Anexos:
- Referencias a release/security-reports/
"@
$securityMdPath = Join-Path $root "release\dossier_security_v1.md"
$automationMdPath = Join-Path $root "release\dossier_automation_v1.md"
$securityMd | Out-File -FilePath $securityMdPath -Encoding utf8 -Force
$automationMd | Out-File -FilePath $automationMdPath -Encoding utf8 -Force

# 11) Create a lightweight README update to document the immediate steps
$readmeAdd = @"
## Quickstart local (generated)
1. Copy `local.settings.json.example` to `local.settings.json` and fill placeholders using Key Vault references.
2. Activate venv: `& .\.venv\Scripts\Activate.ps1`
3. Start local environment: `.\start-local.ps1` (or use VS Code Task: Start VRTX Sentinel Local)
4. Use mocks in `mocks/` to avoid external credits consumption. Set ENABLE_LLM=false for dev.
"@
Add-Content -Path (Join-Path $root "README.md") -Value $readmeAdd

# 12) Git add & commit changes (safe, minimal message)
git add -A
git commit -m "chore(modular): scaffold modular structure, feature flags, mocks, start script, tasks and dossiers" 2>$null

# 13) Final output summary
Write-Output "=== SETUP COMPLETE ==="
Write-Output "Root: $root"
Write-Output "Start script: $startScriptPath"
Write-Output "VS Code Task: $tasksJsonPath"
Write-Output "Local settings example: $localExamplePath"
Write-Output "Mocks: $openaiMockPath , $adxMockPath"
Write-Output "Dossiers (markdown): $securityMdPath , $automationMdPath"
Write-Output "Release folder: $release"
Write-Output "Git branch: refactor/modular (checked out)"
Write-Output "Next steps:"
Write-Output "  1) Edit local.settings.json.example -> local.settings.json with Key Vault placeholders (do NOT commit secrets)."
Write-Output "  2) Activate venv and run .\start-local.ps1 or use the VS Code Task."
Write-Output "  3) Test endpoints locally and keep ENABLE_LLM=false to save credits."
