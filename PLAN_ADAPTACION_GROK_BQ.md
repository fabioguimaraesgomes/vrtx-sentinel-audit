# Plan: adaptar propuesta Grok → VRTX Sentinel local

**Fecha:** 2026-09-13  
**Decisión Miney (autonomía Fabio):** base = `C:\VRTX-SENTINEL Simulador`  
**No usar como base:** `C:\vrtx-sentinel-azure-final` (stack Azure ADX/Event Grid/Azure OpenAI; útil solo como donante de patrones).

## Por qué Simulador

| Criterio | Simulador | azure-final |
|----------|-----------|-------------|
| BigQuery / GCP | Sí (`main.py` + `google-cloud-bigquery`) | No (ADX/Kusto) |
| Alineación con Grok↔BQ MCP + proyecto `gen-lang-client-0320924150` | Alta | Baja |
| Arranque local / mocks | Sí | Functions Azure + Azurite |
| Madurez Functions/CI/security utils | Media (docs + CI) | Alta (migración completa, tests) |

Grok propone orquestar consultas BQ, telemetría, exports de auditoría, costes y alertas. Eso encaja con el ADN GCP del Simulador, no con ADX.

## Qué reutilizar de azure-final (sin cambiar de cloud)

- Estructura modular `extract_telemetry` / `run_inference` / `publish_event` / `copilot_adapter`
- Utilidades de seguridad (rate limit, idempotency, headers) si aplican
- Ideas de CI (semgrep/pip-audit) ya esbozadas en Simulador

## Arquitectura objetivo (adaptada)

```
BigQuery (gen-lang-client-0320924150)
    │
    ├─ Grok.com connector (MCP)  → consultas interactivas / exploración
    │
    └─ VRTX-SENTINEL Simulador (local → Cloud Functions/Run)
           extract_telemetry (SQL BQ)
           → run_inference (LLM: Gemini o xAI según flag)
           → publish_event (webhook/PubSub/JSON alert)
```

## Fases

### Fase 0 — Conector Grok (en curso)
- [ ] Completar Allow OAuth BigQuery en grok.com/connectors
- [ ] Smoke: listar datasets/tablas del proyecto desde Grok

### Fase 1 — Datos reales en Simulador
- [ ] `GCP_PROJECT_ID=gen-lang-client-0320924150` en local.settings / env
- [ ] Credencial ADC o service account (sin secretos en git)
- [ ] Query real en `extract_telemetry` (sustituir telemetría hardcodeada de `main.py`)
- [ ] Dataset/tabla de auditoría o mock table si aún no hay logs

### Fase 2 — Inferencia y alertas
- [ ] Flag `LLM_PROVIDER=gemini|xai|off`
- [ ] Salida JSON estricta (`SEGURO` / `BRECHA_DETECTADA` / riesgo)
- [ ] `publish_event` a archivo local + webhook opcional

### Fase 3 — Observabilidad Grok-style
- [ ] Export métricas/costes BQ (INFORMATION_SCHEMA / jobs)
- [ ] Dashboard mínimo (CSV/Looker Studio o query guardada)
- [ ] Alertas por umbral (job fallido, coste día, evento crítico)

## Fuera de alcance inmediato
- Re-migrar todo a Azure ADX
- Publicar cloud sin Allow OAuth + ADC
- IURIS / Readdy (van después)

## Primera acción de código (siguiente)
1. Módulo `services/bq_client.py` con list_datasets / run_query read-only  
2. Actualizar `main.py` para usar proyecto real + modo `ENABLE_LLM=false`  
3. Script `scripts/smoke_bq.py` para probar ADC contra el proyecto Gemini

---

## Síntesis del chat Grok (2026-09-13) — leído por Miney

### Arquitectura que Grok recomienda (adoptada)
- **GCP:** BigQuery, Functions/Run, Scheduler, IAM, VPC, logs, secretos, producción
- **xAI:** modelo (`grok-4.6`), function calling, RAG/Collections, análisis
- **GitHub/Vercel:** código, portal, deploys
- **Stripe:** cobro (más adelante)
- **No** migrar toda la infra de GCP a xAI

### Producto SaaS (visión)
Pedido auditoría → ingestión export → checks → findings → score → informe PDF/JSON → dashboard → cobro  
Funciones: `list_scope`, `ingest_export`, `run_checks`, `score_findings`, `draft_report`

### Capas IA
- Sustituir Gemini por capa proveedor → `grok-4.6` + JSON estricto
- Collections: `vrtx-audit-kb` + colección por cliente
- Gmail automation `vrtx-pedido-auditoria`: borradores, **nunca envío automático**

### BigQuery connector (estado)
- Sigue **desconectado** en grok.com/connectors
- Intentos previos: timeout
- Grok advierte: preferir conector oficial Grok/xAI; **no** depender de client_secret propio pegado en chat
- Si se pegó un OAuth client secret en el chat de Grok → **revocar/rotar** en GCP Console

### Ajuste al plan Miney
1. Backup/rama canónica (no sobrescribir azure-final)
2. Esquema común AuditRequest / Evidence / Finding / Score / Report / Alert
3. Ingestión CSV/JSON/PDF primero; BQ como backend de evidencias/métricas
4. Checks deterministas IAM/VPC/exposición/costes
5. Adaptador xAI + flag `LLM_PROVIDER`
6. Dashboard + alertas + intake Gmail (borrador)
