targetScope = 'resourceGroup'

@description('Azure location')
param location string

@description('Environment suffix')
param environment string

@description('Prefix for all resource names')
param namePrefix string

@secure()
@description('AAD object ID for deployment principal with Key Vault admin rights')
param keyVaultAdminObjectId string

@description('OpenAI endpoint to keep as configuration secret')
param openAiEndpoint string

var keyVaultName = '${namePrefix}-${environment}-kv'

resource keyVault 'Microsoft.KeyVault/vaults@2024-11-01' = {
  name: keyVaultName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enabledForTemplateDeployment: true
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }
}

resource kvAdminRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, keyVaultAdminObjectId, 'Key Vault Administrator')
  scope: keyVault
  properties: {
    principalId: keyVaultAdminObjectId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '00482a5a-887f-4fb3-b363-3b7fe8e74483')
    principalType: 'ServicePrincipal'
  }
}

resource openAiEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' = {
  parent: keyVault
  name: 'openai-endpoint'
  properties: {
    value: openAiEndpoint
  }
  dependsOn: [
    kvAdminRoleAssignment
  ]
}

output keyVaultUri string = keyVault.properties.vaultUri
