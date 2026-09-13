# QA Simulado VRTX Sentinel — 2026-09-13

**Rama:** eat/xai-draft-report  
**Host:** DESKTOP-966MIVV (C:\VRTX-SENTINEL Simulador)  
**Python:** C:\Users\VRTXCLOUD\AppData\Local\Python\pythoncore-3.14-64\python.exe  
**LLM:** LLM_PROVIDER=off (sin red / sin xAI)

## Tests ejecutados

| Suite | Resultado |
|-------|-----------|
| scripts/smoke_ingest.py | OK — score **27.0**, grade F, 4 findings, 4 remediations |
| scripts/qa_simulado.py | OK — **13/13 PASS** |

### Casos en qa_simulado.py

1. Happy path sample_iam.json (score 27)
2. JSON lista vacia []
3. CSV vacio
4. JSON malformado → ValueError limpio (sin traceback de json)
5. Ruta inexistente → FileNotFoundError claro
6. CSV con filas IAM/storage/vpc
7. Auth-log con ailed_auth >= 3 → VRTX-AUTH-FAILED-BURST
8. Auth-log con < 3 fallos → sin burst
9. draft_report: titulo no vacio, remediaciones por codigo, JSON serializable
10. LLM_PROVIDER=off nunca llama a red (urlopen monkeypatch)
11. Ruta con espacios (path with spaces/auth low.json)
12. Evidence.payload=None no rompe checks/score/report
13. Encoding no UTF-8 → ValueError limpio

## Fallos encontrados

1. **JSON malformado** elevaba json.JSONDecodeError crudo (traceback de libreria).
2. **Fichero no UTF-8** elevaba UnicodeDecodeError crudo.
3. **Evidence.payload=None** provocaba AttributeError en _check_public_buckets (.get).
4. **CSV vacio** devolvia [{}] (evidencia fantasma) en lugar de lista vacia como JSON [].
5. **score_findings(None) / 
un_checks(None) / draft_report(None, …)** lanzaban TypeError al iterar.
6. **Score.grade=None** producia titulo grado None.

## Fixes aplicados

| Modulo | Cambio |
|--------|--------|
| services/ingest.py | ValueError tipado para JSON malformado y encoding; CSV vacio → []; 
ull JSON → payload {}; inferencia uth por nombre/claves |
| services/checks_basic.py | Coercion de evidences None; skip evidences None; payload no-dict → {} antes de checkers |
| services/score.py | Acepta indings=None; filtra entradas None |
| services/report.py | Findings/score None-safe; titulo/resumen con grade/total por defecto; remediaciones tolerantes |
| scripts/qa_simulado.py | Suite QA amplia (nueva) |
| mocks/fixtures/* | empty_list.json, empty.csv, malformed.json, sample_iam_rows.csv, uth_burst.json, uth_low.json, path with spaces/auth low.json |

## Numeros finales smoke (LLM_PROVIDER=off)

- **evidences:** 3  
- **findings_count:** 4 (VRTX-IAM-OWNER, VRTX-IAM-PRIMITIVE, VRTX-STORAGE-PUBLIC, VRTX-NET-EXTERNAL-IP)  
- **score.total:** **27.0**  
- **score.grade:** F  
- **by_severity:** critical=2, high=1, medium=1  
- **remediations:** 4  

## Riesgos residuales

- Heuristicas IAM/storage/IP son best-effort sobre payloads heterogeneos; falsos positivos/negativos posibles en CSV pobremente tipados.
- LLM_PROVIDER=xai no se ejercita en CI/smoke (intencional); fallos de red/API se tragan en el adaptador.
- venv local puede estar roto; se uso Python del sistema 3.14 — conviene regenerar .venv antes de demos.
- No se toco zure-final ni se anadieron secretos.
- Regla auth-burst depende de claves/eventos reconocibles; logs con esquemas desconocidos no disparan finding.

## Como repetir

`
set LLM_PROVIDER=off
python scripts/smoke_ingest.py
python scripts/qa_simulado.py
`
