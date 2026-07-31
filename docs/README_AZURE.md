# VRTX-SENTINEL Azure Final

Migracion completa de VRTX-SENTINEL al ecosistema Microsoft Azure y Copilot Security.

## Componentes principales
- Azure Functions (Python 3.10): extraccion, inferencia, publicacion y adaptador Copilot.
- Azure Data Explorer (ADX): almacenamiento y consultas de telemetria.
- Azure OpenAI (GPT-4.1 / GPT-4o): inferencia autonoma de riesgo.
- Event Grid: publicacion de eventos de riesgo.
- Zero-Trust: Managed Identity, Key Vault, JWT estricto, logs JSON.
- IaC: Bicep modular para recursos core.

## Flujo funcional
1. `extract_telemetry` consulta ADX via KQL.
2. `run_inference` triangula desvio + IA.
3. `publish_event` emite evento normalizado a Event Grid.
4. `copilot_adapter` entrega payload compatible con Copilot Security.

## Requisitos
- Python 3.10+
- Azure CLI
- Bicep CLI (incluido con Azure CLI moderno)

## Desarrollo local
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
pytest
```
