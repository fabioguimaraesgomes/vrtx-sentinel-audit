# Guia de Despliegue Azure

## 1. Preparar entorno
```bash
az login
az account set --subscription <subscription-id>
```

## 2. Variables
- `RG_NAME`: resource group destino.
- `LOCATION`: region Azure.
- `KV_ADMIN_OBJECT_ID`: object id con permisos de admin para Key Vault.
- `OPENAI_ENDPOINT`: endpoint de Azure OpenAI.

## 3. Validar IaC
```bash
cd infra/scripts
chmod +x validate.sh deploy.sh
./validate.sh "$RG_NAME" "$LOCATION"
```

## 4. Desplegar recursos
```bash
./deploy.sh "$RG_NAME" "$LOCATION" "$KV_ADMIN_OBJECT_ID" "$OPENAI_ENDPOINT"
```

## 5. Publicar Azure Functions
```bash
func azure functionapp publish <function-app-name> --python
```

## 6. Configurar secretos en Key Vault
Agregar secretos requeridos:
- `adx-app-id`
- `adx-app-key`
- `eventgrid-topic-key`
- `openai-key`

## 7. Verificacion
- Probar endpoint `POST /api/extract-telemetry`
- Probar endpoint `POST /api/run-inference`
- Probar endpoint `POST /api/publish-event`
- Probar endpoint `POST /api/copilot-adapter`
