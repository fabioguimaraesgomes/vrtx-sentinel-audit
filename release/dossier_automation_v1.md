# Dossier Automation - VRTX Sentinel
Version: v1
Resumen ejecutivo:
- PropÃ³sito: Automatizar controles, orquestaciÃ³n y publicaciÃ³n de eventos.
- MÃ³dulos incluidos: reglas, playbooks, publish_event, integraciÃ³n Event Grid/ADX (stubs en dev).
Runbook de arranque local:
1. Copiar local.settings.json.example -> local.settings.json y activar ENABLE_AUTOMATION=true
2. Ejecutar .\start-local.ps1
3. Probar endpoint: http://localhost:7071/api/publish_event
Anexos:
- Referencias a release/security-reports/
