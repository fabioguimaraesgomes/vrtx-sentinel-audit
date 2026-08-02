# Manual de Curaduría y Auditoría Operativa VRTX Sentinel

**Versión:** v1.0  
**Fecha:** 2026-08-02  
**Responsable:** Fabio Guimaraes (fabioguimaraesgomes)  
**Repositorio:** https://github.com/fabioguimaraesgomes/vrtx-sentinel-audit

## 1. Objetivo del manual
Este documento centraliza los accesos operativos, módulos, rutas y pasos de auditoría de VRTX Sentinel Audit para curaduría técnica. Está diseñado para ejecución local y controlada.

## 2. Política de seguridad de accesos
- Este manual no contiene secretos reales.
- Todas las claves y contraseñas se representan con placeholders.
- Inyección de secretos: Azure Key Vault + Managed Identity.

## 3. Claves de acceso (placeholders)
- AZURE_OPENAI_ENDPOINT: <AZURE_OPENAI_ENDPOINT_PLACEHOLDER>
- AZURE_OPENAI_KEY: <KEY_IN_KEYVAULT_PLACEHOLDER>
- ADX_CLUSTER: <ADX_CLUSTER_PLACEHOLDER>
- ADX_DATABASE: <ADX_DATABASE_PLACEHOLDER>
- KEY_VAULT_NAME: <KEY_VAULT_NAME_PLACEHOLDER>
- MI_PRINCIPAL_ID: <MANAGED_IDENTITY_PRINCIPAL_ID_PLACEHOLDER>

## 4. Módulos del SaaS
### 4.1 Security
- Ruta modular: services/security/extract_telemetry/
- Endpoint validado: POST /api/extract_telemetry
- Estado: operativo en stub local.

### 4.2 Automation
- Rutas modulares:
  - services/automation/publish_event/
  - services/automation/run_inference/
- Endpoints:
  - POST /api/publish_event
  - POST /api/run_inference
- Estado: publish_event validado en stub local; run_inference disponible.

### 4.3 Integration
- Ruta modular: services/integration/copilot_adapter/
- Endpoint: POST /api/copilot_adapter
- Estado: disponible para integración local.

### 4.4 Deception
- Ruta objetivo: services/deception/
- Estado: desactivado por defecto.
- Flag: ENABLE_DECEPTION=false

## 5. Rutas de ejecución local
### 5.1 Archivos críticos
- host.json
- local.settings.json.example
- start-local.ps1
- .github/workflows/ci-security.yml
- docs/security-runbook.md
- docs/plan-modular-2-semanas.md

### 5.2 Endpoints operativos locales
- Base URL: http://localhost:7071
- http://localhost:7071/api/extract_telemetry
- http://localhost:7071/api/publish_event
- http://localhost:7071/api/run_inference
- http://localhost:7071/api/copilot_adapter

### 5.3 Comandos de arranque
1. Activación:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& .\.venv\Scripts\Activate.ps1

2. Arranque:
.\start-local.ps1

3. Smoke tests:
curl.exe -X POST http://localhost:7071/api/extract_telemetry -H "Content-Type: application/json" -d '{"test":"ok"}'
curl.exe -X POST http://localhost:7071/api/publish_event -H "Content-Type: application/json" -d '{"event":"test"}'

## 6. Evidencia operativa actual
- extract_telemetry: HTTP 200 con respuesta stubbed.
- publish_event: HTTP 200 con respuesta stubbed.

## 7. CI, gating y control de publicación
- Workflow: .github/workflows/ci-security.yml
- Controles activos:
  - ruff
  - pytest
  - semgrep
  - pip-audit
- Bloqueo crítico: CVSS >= 9.0 via check_pip_audit_critical.py

## 8. Checklist de curaduría para publicar
- [ ] Branch protection con checks requeridos.
- [ ] Reportes en release/security-reports/:
  - semgrep.json
  - zap_report.json
  - pip-audit.json
- [ ] Key Vault configurado y secretos cargados.
- [ ] Managed Identity con permisos mínimos.
- [ ] Staging con ENABLE_LLM=false inicial.

## 9. Faltantes detectados
- release/security-reports/semgrep.json
- release/security-reports/zap_report.json
- release/security-reports/pip-audit.json
- migration_report_azure.json

## 10. Conclusión
El SaaS está funcional y operativo en modo local stub para auditoría técnica inmediata. La publicación controlada requiere completar evidencias de seguridad y cierre de secretos con Key Vault/Managed Identity.
