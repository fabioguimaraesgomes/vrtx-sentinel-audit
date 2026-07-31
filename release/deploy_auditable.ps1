param(
  [Parameter(Mandatory = $true)]
  [string]$SubscriptionId,
  [string]$ResourceGroup = "vrtx-sentinel-rg-stg",
  [string]$Location = "westeurope",
  [string]$FunctionAppName = "vrtx-stg-func",
  [string]$KeyVaultName = "vrtx-stg-kv",
  [string]$AdxClusterName = "vrtx-stg-adx",
  [string]$AdxDatabaseName = "vrtxsentinel"
)

$ErrorActionPreference = "Stop"
$az = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"

if (-not (Test-Path $az)) {
  throw "No se encontro Azure CLI en ruta esperada: $az"
}

Write-Host "[1/9] Seleccionando suscripcion..."
& $az account set --subscription $SubscriptionId

Write-Host "[2/9] Creando RG con tags auditable..."
& $az group create --name $ResourceGroup --location $Location --tags owner=Fabio project=vrtx-sentinel env=stg deployedBy=copilot

Write-Host "[3/9] Validando Bicep..."
& $az deployment group validate --resource-group $ResourceGroup --template-file infra/bicep/main.bicep --parameters @infra/parameters/dev.json

Write-Host "[4/9] Desplegando Bicep..."
& $az deployment group create --resource-group $ResourceGroup --template-file infra/bicep/main.bicep --parameters @infra/parameters/dev.json

Write-Host "[5/9] Verificaciones rapidas de recursos..."
& $az kusto cluster show --resource-group $ResourceGroup --name $AdxClusterName
& $az kusto database show --resource-group $ResourceGroup --cluster-name $AdxClusterName --name $AdxDatabaseName
& $az keyvault show --resource-group $ResourceGroup --name $KeyVaultName
& $az functionapp show --resource-group $ResourceGroup --name $FunctionAppName

Write-Host "[6/9] Managed Identity de Function App..."
& $az functionapp identity assign --resource-group $ResourceGroup --name $FunctionAppName
$principalId = (& $az functionapp identity show --resource-group $ResourceGroup --name $FunctionAppName --query principalId -o tsv)

Write-Host "[7/9] Politica Key Vault para Managed Identity..."
& $az keyvault set-policy --name $KeyVaultName --object-id $principalId --secret-permissions get list

Write-Host "[8/9] Publicando Function App..."
func azure functionapp publish $FunctionAppName --python

Write-Host "[9/9] Endpoint copilot_adapter listo para prueba"
$hostName = (& $az functionapp show --resource-group $ResourceGroup --name $FunctionAppName --query defaultHostName -o tsv)
Write-Host "URL: https://$hostName/api/copilot-adapter"

Write-Host "Despliegue seguro, repetible y auditable completado."
