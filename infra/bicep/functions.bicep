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

@description('Allowed CORS origins for API access')
param corsAllowedOrigins array = []

var storageName = toLower(replace('${namePrefix}${environment}funcst', '-', ''))
var planName = '${namePrefix}-${environment}-asp'
var appInsightsName = '${namePrefix}-${environment}-appi'
var functionAppName = '${namePrefix}-${environment}-func'
var deploymentContainerName = 'app-package'
var storageBlobDataOwnerRoleId = 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
var storageQueueDataContributorId = '974c5e8b-45b9-4653-ba55-5f855dd0fb88'
var storageTableDataContributorId = '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3'

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
    allowSharedKeyAccess: false
    defaultToOAuthAuthentication: true
    publicNetworkAccess: 'Enabled'
  }
}

resource storageBlobServices 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'

  resource deploymentContainer 'containers@2023-05-01' = {
    name: deploymentContainerName
    properties: {
      publicAccess: 'None'
    }
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

resource functionIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${namePrefix}-${environment}-uai'
  location: location
}

resource storageBlobDataOwnerRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, storage.id, functionIdentity.id, storageBlobDataOwnerRoleId)
  scope: storage
  properties: {
    principalId: functionIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataOwnerRoleId)
  }
}

resource storageQueueDataContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, storage.id, functionIdentity.id, storageQueueDataContributorId)
  scope: storage
  properties: {
    principalId: functionIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageQueueDataContributorId)
  }
}

resource storageTableDataContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, storage.id, functionIdentity.id, storageTableDataContributorId)
  scope: storage
  properties: {
    principalId: functionIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageTableDataContributorId)
  }
}

resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: planName
  location: location
  sku: {
    name: 'FC1'
    tier: 'FlexConsumption'
  }
  kind: 'functionapp'
  properties: {
    reserved: true
    maximumElasticWorkerCount: 1
  }
}

resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${functionIdentity.id}': {}
    }
  }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${storage.properties.primaryEndpoints.blob}${deploymentContainerName}'
          authentication: {
            type: 'UserAssignedIdentity'
            userAssignedIdentityResourceId: functionIdentity.id
          }
        }
      }
      scaleAndConcurrency: {
        maximumInstanceCount: 100
        instanceMemoryMB: 2048
      }
      runtime: {
        name: 'python'
        version: '3.10'
      }
    }
  }
}

resource functionAppSettings 'Microsoft.Web/sites/config@2023-12-01' = {
  parent: functionApp
  name: 'appsettings'
  properties: {
    AzureWebJobsStorage__accountName: storage.name
    AzureWebJobsStorage__credential: 'managedidentity'
    AzureWebJobsStorage__clientId: functionIdentity.properties.clientId
    APPLICATIONINSIGHTS_CONNECTION_STRING: appInsights.properties.ConnectionString
    APPLICATIONINSIGHTS_AUTHENTICATION_STRING: 'ClientId=${functionIdentity.properties.clientId};Authorization=AAD'
    KEYVAULT_URI: keyVaultUri
    EVENTGRID_TOPIC_ENDPOINT: eventGridTopicEndpoint
    ADX_CLUSTER_URI: adxClusterUri
    ADX_DATABASE: adxDatabase
    AZURE_OPENAI_ENDPOINT: openAiEndpoint
    CORS_ALLOWED_ORIGINS: join(corsAllowedOrigins, ',')
    SECURITY_CSP: 'default-src none; frame-ancestors none; base-uri none; form-action none;'
    RATE_LIMIT_PER_MINUTE: '120'
    IDEMPOTENCY_TTL_SECONDS: '600'
  }
  dependsOn: [
    storageBlobServices
    storageBlobDataOwnerRoleAssignment
    storageQueueDataContributorRoleAssignment
    storageTableDataContributorRoleAssignment
  ]
}

output functionAppName string = functionApp.name
