targetScope = 'resourceGroup'

@description('Azure location')
param location string

@description('Environment suffix')
param environment string

@description('Prefix for all resource names')
param namePrefix string

@description('Key Vault URI')
param keyVaultUri string

@description('Event Grid topic endpoint')
param eventGridTopicEndpoint string

@description('ADX cluster URI')
param adxClusterUri string

@description('ADX database name')
param adxDatabase string

@description('Azure OpenAI endpoint')
param openAiEndpoint string

var storageName = toLower(replace('${namePrefix}${environment}funcst', '-', ''))
var planName = '${namePrefix}-${environment}-asp'
var appInsightsName = '${namePrefix}-${environment}-appi'
var functionAppName = '${namePrefix}-${environment}-func'

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
  }
}

resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: planName
  location: location
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  kind: 'functionapp'
}

resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.10'
      appSettings: [
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storage.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${listKeys(storage.id, storage.apiVersion).keys[0].value}'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'KEYVAULT_URI'
          value: keyVaultUri
        }
        {
          name: 'EVENTGRID_TOPIC_ENDPOINT'
          value: eventGridTopicEndpoint
        }
        {
          name: 'ADX_CLUSTER_URI'
          value: adxClusterUri
        }
        {
          name: 'ADX_DATABASE'
          value: adxDatabase
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: openAiEndpoint
        }
      ]
    }
  }
}

output functionAppName string = functionApp.name
