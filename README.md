# VRTX-SENTINEL: Auditoría Cognitiva Antifraude

Microservicio *serverless* diseñado bajo el paradigma **Zero-Trust**. Actúa como un centinela autónomo que extrae telemetría de Google BigQuery y utiliza modelos generativos (Gemini 1.5) para detectar fraude financiero, smurfing y blanqueo de capitales en tiempo real.

## Arquitectura y Flujo Táctico

1. **Extracción (BigQuery):** Lectura periódica de transacciones marcadas con estado de riesgo crítico en GCP.
2. **Auto-Descubrimiento Cognitivo:** Escaneo dinámico de la API de Vertex/Gemini para inyectar el modelo de lenguaje de mayor capacidad disponible en la región de despliegue.
3. **Análisis Forense:** El LLM evalúa asimetrías transfronterizas, triangulación de divisas y concentración temporal en milisegundos.
4. **Respuesta Estructurada:** Retorno estricto en formato JSON (`FRAUDE_CRITICO` o `RIESGO_MODERADO`) para su integración con sistemas de alerta descendentes (Webhooks/PubSub).

## Stack Tecnológico
* **Runtime:** Python 3.10 (Google Cloud Functions / Cloud Run)
* **Cognición:** `google-generativeai`
* **Datos:** `google-cloud-bigquery`
* **Automatización:** Google Cloud Scheduler (Cron Job)

## Doctrina Operativa
Este sistema rechaza la fricción biológica. No hay intervención humana en el bucle de detección. Las credenciales se inyectan en tiempo de ejecución mediante Variables de Entorno. Cero confianza, orden absoluto.