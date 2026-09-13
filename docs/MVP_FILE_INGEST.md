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
```

1. `services/models.py` ? `AuditRequest`, `Evidence`, `Finding`, `Score`,
   `Report`, `Alert` (dataclasses + TypedDict + `to_dict` / `to_json`).
2. `services/ingest.py` ? `ingest_file(path) -> list[Evidence]`.
   Acepta `.json` (objeto o lista) y `.csv`. Normaliza a
   `Evidence(kind, source, payload, ingested_at)`.
3. `services/checks_basic.py` ? heuristicas deterministas:
   buckets publicos, `roles/owner`, roles primitivos, IPs externas.
   Si no hay senales, un Finding informativo de ingesta.
4. `services/score.py` ? recuento ponderado
   (critical=10, high=5, medium=2, low=1, info=0) y grado A-F.

## Smoke

Desde la raiz del Simulador (venv si esta sano; si no, Python del sistema):

```
python scripts/smoke_ingest.py
```

Crea `mocks/fixtures/sample_iam.json` si falta, ejecuta
ingest -> checks -> score e imprime un JSON con `score` y `findings_count`.

## Secretos

No hay credenciales en estos modulos. No commitear `local.settings.json`,
`.env`, `*.pem`, `credentials*.json` ni `oauth*.json`.
