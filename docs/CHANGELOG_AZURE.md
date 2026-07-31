# Changelog Azure Migration

## 2026-07-31
- Migradas Cloud Functions a Azure Functions Python 3.10.
- Reemplazado BigQuery por ADX client y consultas KQL.
- Reemplazado Gemini por Azure OpenAI (GPT-4.1/GPT-4o).
- Reemplazado PubSub por Event Grid publisher.
- Implementado adaptador Copilot Security con endpoint dedicado.
- Implementada base Zero-Trust (Key Vault, MI, JWT, logs JSON).
- Agregada infraestructura como codigo en Bicep.
- Agregada cobertura inicial de tests unitarios.
- Agregados pipelines CI/CD para GitHub Actions.

## 2026-08-01
- Hardening final aplicado en endpoints HTTP: cabeceras de seguridad, validacion de origen CORS y rate limiting.
- Implementada idempotencia para `publish_event` con TTL configurable.
- ADX client endurecido a autenticacion Managed Identity-only (sin fallback a Azure CLI).
- Parametrizacion IaC para `CORS_ALLOWED_ORIGINS`, `SECURITY_CSP`, `RATE_LIMIT_PER_MINUTE` e `IDEMPOTENCY_TTL_SECONDS`.
- Agregados workflows CI de contingencia para Semgrep y ZAP: `security-semgrep.yml` y `security-zap.yml`.
