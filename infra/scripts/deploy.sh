#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 ]]; then
  echo "Uso: ./deploy.sh <resource-group> <location> <keyvault-admin-object-id> <openai-endpoint>"
  exit 1
fi

RG_NAME="$1"
LOCATION="$2"
KV_ADMIN_OBJECT_ID="$3"
OPENAI_ENDPOINT="$4"

az group create --name "$RG_NAME" --location "$LOCATION"
az deployment group create \
  --resource-group "$RG_NAME" \
  --template-file ../bicep/main.bicep \
  --parameters location="$LOCATION" keyVaultAdminObjectId="$KV_ADMIN_OBJECT_ID" openAiEndpoint="$OPENAI_ENDPOINT"

echo "Despliegue completado"
