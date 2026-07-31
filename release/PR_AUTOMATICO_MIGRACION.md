# Migración completa a Azure + Copilot Security (Autónoma)

## Resumen
Se migró VRTX-SENTINEL desde stack previo a ecosistema Microsoft Azure con foco Zero-Trust y compatibilidad con Copilot Security.

## Artefactos
- Azure Functions Python 3.10: `extract_telemetry`, `run_inference`, `publish_event`, `copilot_adapter`.
- Cliente ADX real con soporte Managed Identity y Key Vault.
- Cliente Azure OpenAI real con GPT-4.1/GPT-4o.
- Cliente Event Grid real para publicación de eventos normalizados.
- Prompt de riesgo y adaptador de inferencia autónoma.
- Adaptador Copilot Security con endpoint HTTP y modo test.
- Bicep modular: Key Vault, ADX, Event Grid, Function App.
- Scripts de validación y despliegue.
- Tests unitarios para clientes y adaptador.
- Pipelines CI/CD en GitHub Actions.

## Checklist
- [x] Estructura de proyecto independiente creada.
- [x] Migración de runtime a Azure Functions.
- [x] Migración BigQuery -> ADX con KQL.
- [x] Migración Gemini -> Azure OpenAI.
- [x] Migración PubSub -> Event Grid.
- [x] Zero-Trust base implementado.
- [x] Adaptador Copilot Security implementado.
- [x] IaC Bicep implementada.
- [x] Tests unitarios pasando.
- [x] Documentación técnica y operativa.

## Instrucciones
1. Configurar remoto GitHub:
   - `git remote add origin <repo-url>`
2. Push de rama:
   - `git push -u origin feature/migracion-azure-copilot-security`
3. Crear PR con este contenido y título:
   - `Migración completa a Azure + Copilot Security (Autónoma)`
