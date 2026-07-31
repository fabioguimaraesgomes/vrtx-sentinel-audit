# Copilot Security Extension Guide

## Objetivo
Transformar reportes VRTX-SENTINEL al contrato estructurado consumible por Copilot Security.

## Endpoint
- Metodo: `POST`
- Ruta: `/api/copilot-adapter`
- Auth: `Bearer JWT`
- Query opcional: `test_mode=true`

## Request esperado
```json
{
  "id": "incident-123",
  "severity": "high",
  "risk_score": 0.82,
  "summary": "Beaconing detectado",
  "evidence": ["Conexiones periodicas a dominio raro"],
  "recommendation": "Bloquear IOC",
  "actionable_steps": ["Aislar host", "Rotar secretos"]
}
```

## Response
```json
{
  "metadata": {},
  "risk": {},
  "evidence": [],
  "recommendation": "",
  "actionable_steps": []
}
```

## Modo test
Con `test_mode=true`, se habilita el token de prueba configurado en la variable de entorno `TEST_MODE_TOKEN` para validaciones en QA.
