targetScope = 'resourceGroup'

@description('Azure location')
param location string

@description('Environment suffix')
param environment string

@description('Prefix for all resource names')
param namePrefix string

var adxClusterName = '${namePrefix}-${environment}-adx'
var adxDatabaseName = 'vrtxsentinel'

resource adxCluster 'Microsoft.Kusto/clusters@2024-04-13' = {
  name: adxClusterName
  location: location
  sku: {
    name: 'Dev(No SLA)_Standard_D11_v2'
    tier: 'Basic'
    capacity: 1
  }
  properties: {
    enableStreamingIngest: true
    publicNetworkAccess: 'Enabled'
  }
}

resource adxDatabase 'Microsoft.Kusto/clusters/databases@2024-04-13' = {
  parent: adxCluster
  name: adxDatabaseName
  location: location
  kind: 'ReadWrite'
  properties: {
    softDeletePeriod: 'P7D'
    hotCachePeriod: 'P1D'
  }
}

output adxClusterUri string = 'https://${adxCluster.name}.kusto.windows.net'
output adxDatabase string = adxDatabase.name
