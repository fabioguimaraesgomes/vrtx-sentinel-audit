# MVP file-first (sin BigQuery)

**Fecha:** 2026-09-13  
**Base:** `C:\VRTX-SENTINEL Simulador`  
**No usar como producto:** `vrtx-sentinel-azure` / azure-final.

## Por que file-first

El proyecto BigQuery `gen-lang-client-0320924150` esta vacio (sin datasets
ni tablas de auditoria). El MVP no espera ADC, exports de Cloud Audit ni
queries SQL. La fuente de verdad es un fichero local **CSV o JSON**.

BigQuery queda como backend opcional de evidencias/metricas en una fase
posterior. `main.py` y los stubs Azure se mantienen; estos modulos se
anaden al lado.

## Flujo

```
CSV/JSON  ->  ingest_file()  ->  Evidence[]
                 |                    |
                 v                    v
           run_checks()  ->  Finding[]  ->  score_findings()  ->  Score
                                              |
                                              v
                                        draft_report()  ->  Report
                                              |
                          (opcional) xai_adapter.maybe_rewrite_summary
```

1. `services/models.py` ? `AuditRequest`, `Evidence`, `Finding`, `Score`,
   `Report`, `Alert` (dataclasses + TypedDict + `to_dict` / `to_json`).
2. `services/ingest.py` ? `ingest_file(path) -> list[Evidence]`.
   Acepta `.json` (objeto o lista) y `.csv`. Normaliza a
   `Evidence(kind, source, payload, ingested_at)`.
3. `services/checks_basic.py` ? heuristicas deterministas:
   buckets publicos, `roles/owner`, roles primitivos, IPs externas.
   Si no hay senales, un Finding informativo de ingesta.
4. `services/score.py` — recuento ponderado
   (critical=10, high=5, medium=2, low=1, info=0) y grado A-F.
5. `services/checks_basic.py` — tambien regla opcional
   `VRTX-AUTH-FAILED-BURST` si el payload parece logs de auth y
   `failed_auth` >= 3 (severity medium/high). Sin Azure/ADX/OpenAI.
6. `services/report.py` — `draft_report(findings, score, *, lang='es',
   client_id=None) -> Report` determinista (titulo, score/grado,
   findings, remediaciones por codigo). No requiere LLM.
7. `services/xai_adapter.py` — opcional. Solo si `LLM_PROVIDER=xai` y
   existe `XAI_API_KEY`: llama a grok-4.6 (`https://api.x.ai/v1`) para
   reescribir **unicamente** el resumen ejecutivo. Nunca inventa
   findings. Por defecto `LLM_PROVIDER=off` (o sin key) -> texto
   determinista sin llamada externa.

## draft_report / LLM_PROVIDER

| Variable | Valores | Efecto |
|----------|---------|--------|
| `LLM_PROVIDER` | `off` (default), `xai` | `off` = solo borrador determinista; `xai` habilita pulido del summary |
| `XAI_API_KEY` | secreto (no commitear) | Requerido junto a `LLM_PROVIDER=xai`; si falta, se omite el LLM |

El smoke fija `LLM_PROVIDER=off` y exige score **27** sobre
`mocks/fixtures/sample_iam.json`.

## Smoke

Desde la raiz del Simulador (venv si esta sano; si no, Python del sistema):

```
python scripts/smoke_ingest.py
```

Crea `mocks/fixtures/sample_iam.json` si falta, ejecuta
ingest -> checks -> score -> draft_report e imprime titulo del report,
conteo de findings y JSON con `score` (assert score == 27 con
`LLM_PROVIDER=off`).

## Secretos

No hay credenciales en estos modulos. No commitear `local.settings.json`,
`.env`, `*.pem`, `credentials*.json` ni `oauth*.json`.
