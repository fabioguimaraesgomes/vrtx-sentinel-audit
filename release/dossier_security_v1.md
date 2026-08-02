# Dossier Security - VRTX Sentinel
Version: v1
Resumen ejecutivo:
- PropÃ³sito: AuditorÃ­a y protecciÃ³n autÃ³noma.
- MÃ³dulos incluidos: detectan fallos, analizan logs, alertan, protegen identidades, zero-trust dinÃ¡mico, deception (desactivado por defecto).
Runbook de arranque local:
1. Copiar local.settings.json.example -> local.settings.json y rellenar placeholders con secretos en Key Vault.
2. Ejecutar .\start-local.ps1
3. Probar endpoint: http://localhost:7071/api/extract_telemetry
Anexos:
- Referencias a release/security-reports/
