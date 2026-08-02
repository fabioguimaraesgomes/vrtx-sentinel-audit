# Backup Manifest VRTX Sentinel Audit

Fecha: 2026-08-02
Rama base: refactor/modular
Objetivo: preservar un snapshot seguro y portable del proyecto antes de iniciar otro.

## Artefactos de respaldo
- release/vrtx_sentinel_audit_v1.0.0.bundle
- release/vrtx_sentinel_audit_workspace_safe_backup_v1.0.0.zip
- release/release_v1.0.0.zip

## Contenido esperado
- Código fuente del workspace
- Documentación técnica y operativa
- Scripts de arranque y generación PDF
- Artefactos de release

## Exclusiones del ZIP sanitizado
- .git/
- .venv/
- .venv-1/
- local.settings.json
- __pycache__/
- *.pyc

## Seguridad
- No se incluyen secretos reales en el ZIP sanitizado.
- local.settings.json se excluye explícitamente.
- Los secretos documentados permanecen como placeholders y referencias a Key Vault.
