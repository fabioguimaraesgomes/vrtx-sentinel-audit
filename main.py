import functions_framework
from google.cloud import bigquery
import google.generativeai as genai
import os
import json

# ==========================================
# // CONFIGURACIÓN ZERO-TRUST
# Las credenciales nunca se escriben en el código.
# Se inyectarán como Variables de Entorno en GCP.
# ==========================================
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "tu-proyecto-vrtx")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "CLAVE_NO_CONFIGURADA")

# Inicialización de clientes
bq_client = bigquery.Client(project=PROJECT_ID)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro') # El modelo táctico

# ==========================================
# // DIRECTRIZ DEL SISTEMA (PROMPT MILITAR)
# ==========================================
SYSTEM_PROMPT = """
Eres VRTX-SENTINEL, un auditor de ciberseguridad Zero-Trust. 
Analiza los siguientes registros crudos de VPC y accesos IAM.
Busca patrones de escalada de privilegios, intentos anómalos o escaneos desde IPs no autorizadas.
Si el sistema está comprometido, devuelve un JSON con 'estado': 'BRECHA_DETECTADA' y el análisis.
Si todo es normal, devuelve un JSON con 'estado': 'SEGURO'.
Sé frío, exacto y no incluyas texto fuera del formato JSON.
"""

@functions_framework.http
def sentinel_audit(request):
    """Punto de entrada HTTP para la Cloud Function."""
    
    # 1. EXTRACCIÓN DE TELEMETRÍA (Simulada para la primera fase)
    # Aquí irá la query real a BigQuery para leer los VPC Flow Logs
    query = """
        SELECT timestamp, resource.labels.project_id, jsonPayload
        FROM `tu-proyecto-vrtx.audit_logs.cloudaudit_googleapis_com_data_access`
        ORDER BY timestamp DESC
        LIMIT 100
    """
    
    # Por ahora, inyectamos un payload de prueba para calibrar la IA
    test_telemetry = """
    [2026-06-25 18:00:01] INFO: IAM_AUTH_SUCCESS | USER: admin | IP: KNOWN_NET
    [2026-06-25 18:00:05] WARN: IAM_AUTH_FAIL | USER: root | IP: 192.168.1.50
    [2026-06-25 18:00:06] WARN: IAM_AUTH_FAIL | USER: root | IP: 192.168.1.50
    [2026-06-25 18:00:07] CRIT: IAM_AUTH_FAIL | USER: root | IP: TOR_EXIT_NODE
    """

    try:
        # 2. INYECCIÓN COGNITIVA (Llamada a Gemini)
        prompt = f"{SYSTEM_PROMPT}\n\n[TELEMETRÍA RECIENTE]:\n{test_telemetry}"
        response = model.generate_content(prompt)
        
        # 3. RESPUESTA TÁCTICA
        # Parseamos la respuesta para asegurar que es un JSON limpio
        resultado = json.loads(response.text.replace("```json", "").replace("```", ""))
        
        return (json.dumps(resultado), 200, {'Content-Type': 'application/json'})

    except Exception as e:
        # Control de fallos
        error_msg = {"estado": "ERROR_DEL_SISTEMA", "detalle": str(e)}
        return (json.dumps(error_msg), 500, {'Content-Type': 'application/json'})