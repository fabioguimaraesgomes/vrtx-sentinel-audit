# Security Runbook: Secrets and Managed Identity

## Objetivo
Definir el flujo seguro para manejo de secretos en desarrollo local y despliegues cloud.

## 1) Desarrollo local (sin exponer secretos)
1. Copiar local.settings.json.example a local.settings.json.
2. Mantener ENABLE_LLM=false por defecto en desarrollo.
3. No almacenar llaves reales en el repositorio.
4. Usar variables de entorno locales para pruebas controladas.

Ejemplo PowerShell local:
- $env:AZURE_OPENAI_ENDPOINT="https://<tu-endpoint>.openai.azure.com/"
- $env:AZURE_OPENAI_KEY="<solo-local-no-commit>"
- $env:ADX_CLUSTER="https://<tu-cluster>.<region>.kusto.windows.net"
- $env:ADX_DATABASE="<tu-db>"

## 2) Producción y preproducción con Managed Identity
1. Habilitar System Assigned Managed Identity en la app de despliegue.
2. Crear Azure Key Vault en el entorno controlado.
3. Guardar secretos en Key Vault.
4. Conceder permisos de lectura de secretos a la identidad administrada de la app.
5. Referenciar secretos por nombre desde configuración de aplicación.

## 3) Comandos de referencia (Azure CLI)
Crear Key Vault:
- az keyvault create --name <kv-name> --resource-group <rg> --location <region>

Crear secretos:
- az keyvault secret set --vault-name <kv-name> --name AZURE-OPENAI-ENDPOINT --value "https://<endpoint>.openai.azure.com/"
- az keyvault secret set --vault-name <kv-name> --name AZURE-OPENAI-KEY --value "<secret>"

Asignar permisos a Managed Identity (RBAC recomendado):
- az role assignment create --assignee <principal-id-mi> --role "Key Vault Secrets User" --scope $(az keyvault show --name <kv-name> --query id -o tsv)

## 4) Política operativa
- Nunca commitear local.settings.json.
- Rotar secretos periódicamente.
- Habilitar alertas ante intentos de acceso fallidos a Key Vault.
- Mantener logs de acceso a secretos con retención definida.
