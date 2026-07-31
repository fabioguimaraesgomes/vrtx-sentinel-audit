# Security Blocker - Final Gate

Fecha: 2026-08-01

## Estado

La publicacion automatica queda bloqueada hasta completar controles criticos pendientes en CI:

1. Semgrep local no ejecutable de forma estable en este host Windows por resolucion pesada de dependencias.
2. DAST local (OWASP ZAP) no ejecutable por ausencia de Docker/ZAP en el host.
3. No hay remote `origin` configurado en este repo local.
4. `gh` no esta instalado, por lo que no se pueden gestionar repository secrets desde CLI en este host.
5. Azure CLI queda bloqueada por `AADSTS530035` al intentar operaciones con scope de administracion.

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

## Estado operativo actual

- IaC validado localmente tras corregir Bicep, pero el despliegue a Azure sigue bloqueado por credenciales/politicas de acceso.
- Smoke test remoto de `copilot_adapter` sigue devolviendo 500 y requiere despliegue funcional en staging para revalidacion.
