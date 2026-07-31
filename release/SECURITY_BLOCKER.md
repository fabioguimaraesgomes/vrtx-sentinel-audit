# Security Blocker - Final Gate

Fecha: 2026-08-01

## Estado

La publicacion automatica queda bloqueada hasta completar controles criticos pendientes en CI:

1. Semgrep local no ejecutable de forma estable en este host Windows por resolucion pesada de dependencias.
2. DAST local (OWASP ZAP) no ejecutable por ausencia de Docker/ZAP en el host.

## Accion aplicada

- Se crearon workflows CI para desbloquear ejecucion fuera del host local:
  - `pipelines/.github/workflows/security-semgrep.yml`
  - `pipelines/.github/workflows/security-zap.yml`

## Criterio de desbloqueo

- `semgrep-ci.json` sin findings criticos.
- `zap_report.json` con High/Critical = 0.
- `pytest`, `bandit`, `pip-audit` verdes (ya cumplido localmente).

## Publicacion

No publicar hasta completar el criterio de desbloqueo anterior.
