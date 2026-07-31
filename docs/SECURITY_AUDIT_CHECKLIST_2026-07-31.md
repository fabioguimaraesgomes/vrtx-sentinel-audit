# Security Audit Checklist - 2026-07-31

Proyecto auditado: c:\vrtx-sentinel-azure-final

## Evidencia ejecutada

- `pytest -q` -> `4 passed`
- `bandit -r src` -> `No issues identified`
- `pip-audit -r requirements.txt` -> `No known vulnerabilities found`
- `npm audit` -> no aplica (no existe `package.json`)

## Checklist priorizado (estado actual)

### Autenticacion y tokens

- [ ] MSAL + PKCE implementado y probado.
  - Hallazgo: no existe frontend con flujo MSAL/PKCE en este repo.
- [x] Tokens no en localStorage.
  - Evidencia: no hay frontend JS/TS en el proyecto.
- [x] JWT validation (issuer, audience, expiry, signature).
  - Evidencia: `src/utils/security.py` valida `iss`, `aud`, `exp`, `iat` y firma HS256.
- [ ] Token revocation/rotation plan.
  - Hallazgo: no hay politica/documento operativo de revocacion/rotacion de JWT.

### CORS y cabeceras

- [ ] CORS restringido a origenes permitidos.
  - Hallazgo: IaC no define lista de origenes permitidos para Function App.
- [ ] CSP aplicado y probado.
  - Hallazgo: no hay frontend/hosting web con CSP configurado.
- [ ] HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy.
  - Hallazgo: no hay configuracion explicita de estas cabeceras en el runtime HTTP.

### Frontend

- [x] No uso de `innerHTML` o `dangerouslySetInnerHTML`.
  - Evidencia: no existe frontend React/JS en este repositorio.
- [ ] SRI en recursos externos.
  - Hallazgo: no aplica por ausencia de frontend, no hay recursos CDN declarados.
- [ ] Sanitizacion de inputs y outputs.
  - Hallazgo: se agrego validacion estricta de payload en APIs, pero no existe capa frontend.
- [ ] Cookies seguras.
  - Hallazgo: no hay autenticacion por cookies en este repo.

### Secrets & Config

- [x] No secretos en repo ni App Settings.
  - Evidencia: no se detectaron secretos hardcodeados en codigo productivo; secretos se referencian por nombres de Key Vault.
  - Nota: `local.settings.json.example` contiene placeholders y debe mantenerse fuera de secretos reales.
- [ ] Key Vault con acceso minimo y soft-delete/purge protection.
  - Hallazgo: RBAC habilitado, pero falta evidencia de purge protection explicita en IaC.
- [ ] Managed Identity usada para ADX/Event Grid.
  - Hallazgo: Event Grid soporta `DefaultAzureCredential`; ADX todavia cae a autenticacion Azure CLI cuando no hay secretos de app.

### APIs / Functions

- [x] Input validation (pydantic/JSON Schema).
  - Evidencia: validacion estricta agregada en `src/utils/schemas.py` y aplicada en `copilot_adapter` y `publish_event`.
- [ ] Rate limiting / throttling.
  - Hallazgo: no existe limitacion por IP/token ni cuotas por endpoint.
- [ ] Idempotency keys.
  - Hallazgo: no hay soporte para `Idempotency-Key`.
- [x] Logs sin PII.
  - Evidencia: logs estructurados; no se registra payload sensible por defecto.

### Dependencies

- [x] pip-audit / npm audit / trivy / snyk reports reviewed.
  - Evidencia: `pip-audit` ejecutado y limpio; `npm audit` no aplica por ausencia de `package.json`.
  - Pendiente: `trivy` y `snyk` no ejecutados en este entorno.
- [ ] Dependabot or scheduled SCA.
  - Hallazgo: no existe `.github/dependabot.yml`.

### DAST / Pentest

- [ ] OWASP ZAP baseline + active scan completed.
  - Hallazgo: no ejecutado aun.
- [ ] Manual pentest for auth flows and token handling.
  - Hallazgo: no ejecutado aun.

### Observability

- [ ] Application Insights + Azure Sentinel ingestion.
  - Hallazgo: Application Insights provisionado; ingestion a Sentinel no verificada en IaC.
- [ ] Alerts for auth failures, spikes, anomalies.
  - Hallazgo: no hay reglas de alerta definidas en IaC.

## Cambios aplicados en esta sesion

- Eliminado token hardcodeado de test en `src/utils/security.py`; ahora usa `TEST_MODE_TOKEN` por entorno.
- Actualizadas dependencias vulnerables en `requirements.txt`:
  - `PyJWT` a `2.13.0`
  - `pytest` a `9.0.3`
- Agregada validacion de payload en APIs:
  - `src/utils/schemas.py`
  - `src/functions/copilot_adapter/__init__.py`
  - `src/functions/publish_event/__init__.py`
- Actualizada documentacion de test token en `docs/COPILOT_EXTENSION_GUIDE.md`.

## Riesgos pendientes de mayor prioridad

1. Definir CORS estricto y cabeceras de seguridad en la Function App.
2. Implementar rate limiting e idempotencia en endpoints publicos.
3. Forzar autenticacion MI para ADX (sin fallback CLI en ejecucion cloud).
4. Configurar Dependabot y escaneos SCA/SAST programados en CI.
5. Ejecutar ZAP y pentest manual autorizado en staging.
