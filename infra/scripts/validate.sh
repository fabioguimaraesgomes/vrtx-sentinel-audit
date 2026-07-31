#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Uso: ./validate.sh <resource-group> <location>"
  exit 1
fi

RG_NAME="$1"
LOCATION="$2"

az bicep version >/dev/null
az deployment group validate \
  --resource-group "$RG_NAME" \
  --template-file ../bicep/main.bicep \
  --parameters location="$LOCATION"

echo "Validacion completada"
