targetScope = 'resourceGroup'

@description('Azure location')
param location string

@description('Environment suffix')
param environment string

@description('Prefix for all resource names')
param namePrefix string

var topicName = '${namePrefix}-${environment}-eg-topic'

resource topic 'Microsoft.EventGrid/topics@2023-12-15-preview' = {
  name: topicName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    inputSchema: 'EventGridSchema'
    publicNetworkAccess: 'Enabled'
  }
}

output topicEndpoint string = topic.properties.endpoint
output topicName string = topic.name
