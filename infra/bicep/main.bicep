targetScope = 'resourceGroup'

@description('Azure location for all resources')
param location string = resourceGroup().location

@description('Environment suffix, e.g. dev/stg/prod')
param environment string = 'dev'

@description('Prefix for all resource names')
param namePrefix string = 'vrtxsentinel'

@secure()
@description('AAD object ID for deployment principal with Key Vault admin rights')
param keyVaultAdminObjectId string

@description('ADX SKU name')
param adxSkuName string = 'Dev(No SLA)_Standard_D11_v2'

@description('Azure OpenAI endpoint')
param openAiEndpoint string

@description('Allowed CORS origins for API access')
param corsAllowedOrigins array = []

module keyvault './keyvault.bicep' = {
  params: {
    location: location
    environment: environment
    namePrefix: namePrefix
    keyVaultAdminObjectId: keyVaultAdminObjectId
    openAiEndpoint: openAiEndpoint
  }
}

module adx './adx.bicep' = {
  params: {
    location: location
    environment: environment
    namePrefix: namePrefix
  }
}

module eventgrid './eventgrid.bicep' = {
  params: {
    location: location
    environment: environment
    namePrefix: namePrefix
  }
}

module functions './functions.bicep' = {
  params: {
    location: location
    environment: environment
    namePrefix: namePrefix
    keyVaultUri: keyvault.outputs.keyVaultUri
    eventGridTopicEndpoint: eventgrid.outputs.topicEndpoint
    adxClusterUri: adx.outputs.adxClusterUri
    adxDatabase: adx.outputs.adxDatabase
    openAiEndpoint: openAiEndpoint
    corsAllowedOrigins: corsAllowedOrigins
  }
}

output keyVaultUri string = keyvault.outputs.keyVaultUri
output functionAppName string = functions.outputs.functionAppName
output adxClusterUri string = adx.outputs.adxClusterUri
output eventGridTopicEndpoint string = eventgrid.outputs.topicEndpoint
