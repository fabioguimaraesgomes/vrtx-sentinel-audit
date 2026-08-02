# Accesos Operativos VRTX Sentinel Audit

**Versión:** v1.0  
**Fecha:** 2026-08-02  
**Autor:** Equipo Técnico VRTX Sentinel

## 1. Estado operativo actual
- Entorno local funcional en modo stub.
- Endpoints validados con HTTP 200:
  - POST /api/extract_telemetry
  - POST /api/publish_event
- Respuestas actuales: payload JSON con stubbed=true.

## 2. Inventario de accesos (sin secretos reales)
### 2.1 Repositorio
- URL remota: https://github.com/fabioguimaraesgomes/vrtx-sentinel-audit.git
- Rama operativa: refactor/modular
- Tag de release: v1.0.0

### 2.2 Endpoints locales
- Base URL: http://localhost:7071
- Extract telemetry: http://localhost:7071/api/extract_telemetry
- Publish event: http://localhost:7071/api/publish_event
- Run inference: http://localhost:7071/api/run_inference
- Copilot adapter: http://localhost:7071/api/copilot_adapter

### 2.3 Tareas operativas de VS Code
- Start VRTX Sentinel Local
- Build VRTX Dossier PDF
- Build VRTX Access PDF

### 2.4 Archivos críticos
- host.json
- local.settings.json.example
- start-local.ps1
- .github/workflows/ci-security.yml
- docs/security-runbook.md
- docs/plan-modular-2-semanas.md

## 3. Credenciales y secretos (política)
No se incluyen secretos reales en este documento.

### 3.1 Placeholders obligatorios
- AZURE_OPENAI_ENDPOINT=<AZURE_OPENAI_ENDPOINT_PLACEHOLDER>
- AZURE_OPENAI_KEY=<KEY_IN_KEYVAULT_PLACEHOLDER>
- ADX_CLUSTER=<ADX_CLUSTER_PLACEHOLDER>
- ADX_DATABASE=<ADX_DATABASE_PLACEHOLDER>

### 3.2 Nombres recomendados en Key Vault
- vrtx-openai-endpoint
- vrtx-openai-key
- vrtx-adx-cluster
- vrtx-adx-database

### 3.3 Inyección de secretos
- Local: variables de entorno para pruebas controladas.
- Staging/Producción: Managed Identity + Key Vault (sin secretos en código ni Git).

## 4. Comandos de operación rápida
### 4.1 Activar entorno
powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& .\.venv\Scripts\Activate.ps1

### 4.2 Arrancar servicio local
powershell
.\start-local.ps1

### 4.3 Smoke tests
powershell
curl.exe -X POST http://localhost:7071/api/extract_telemetry -H "Content-Type: application/json" -d '{"test":"ok"}'
curl.exe -X POST http://localhost:7071/api/publish_event -H "Content-Type: application/json" -d '{"event":"test"}'

## 5. Release y artefactos
- Dossier técnico PDF: diagnostico_vrtx_sentinel_audit_v1.pdf
- Dossier técnico PDF (release): release/diagnostico_vrtx_sentinel_audit_v1.pdf
- Documento de accesos PDF: accesos_operativos_vrtx_v1.pdf
- Documento de accesos PDF (release): release/accesos_operativos_vrtx_v1.pdf
- Paquete release: release/release_v1.0.0.zip

## 6. CI y compuertas mínimas
- Workflow: .github/workflows/ci-security.yml
- Controles activos:
  - ruff
  - pytest
  - semgrep
  - pip-audit
- Regla de bloqueo crítico: CVSS >= 9.0 via check_pip_audit_critical.py

## 7. Faltantes para publicación plena
- release/security-reports/semgrep.json
- release/security-reports/zap_report.json
- release/security-reports/pip-audit.json
- migration_report_azure.json

## 8. Checklist de salida a staging
- [ ] Key Vault creado y secretos cargados.
- [ ] Managed Identity habilitada con permisos mínimos.
- [ ] Branch protection con checks requeridos.
- [ ] Reportes de seguridad adjuntos en release/security-reports.
- [ ] Prueba canary con ENABLE_LLM=false inicial.

## 9. Nota de cumplimiento
Este documento no contiene contraseñas, tokens ni llaves reales.
Todos los datos sensibles se mantienen como placeholders y deben inyectarse desde Key Vault en entornos controlados.
