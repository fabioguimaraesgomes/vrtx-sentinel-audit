# Plan Modular de 2 Semanas

## Alcance
Refactor por dominios en:
- services/security
- services/automation
- services/deception (desactivado por defecto)

## Semana 1
### Día 1-2
- Inventario de funciones actuales y dependencias.
- Congelar contrato de entrada/salida de endpoints críticos.

### Día 3-4
- Mover lógica de seguridad a services/security.
- Crear interfaces internas para extracción de telemetría y evaluación de riesgo.

### Día 5
- Mover automatización a services/automation.
- Encapsular publicación de eventos y reglas de ejecución.

## Semana 2
### Día 6-7
- Implementar services/deception con feature flag apagado por defecto.
- Añadir stubs/mocks para LLM y ADX en entorno dev.

### Día 8-9
- Integrar feature flags por módulo:
  - ENABLE_SECURITY=true
  - ENABLE_AUTOMATION=true
  - ENABLE_DECEPTION=false
  - ENABLE_LLM=false

### Día 10
- Pruebas integradas y hardening:
  - Smoke tests de endpoints.
  - Verificación de CI (lint, tests, Semgrep, pip-audit).
  - Checklist de seguridad y despliegue.

## Definición de terminado
- Código organizado por dominio.
- Feature flags efectivos por módulo.
- Mocks operativos en dev sin consumo de créditos.
- CI verde y sin findings críticos.
