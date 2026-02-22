@description('Location for all resources')
param location string = resourceGroup().location

@description('Tags for resources')
param tags object = {}

@description('Name for the Container Apps Environment')
param containerAppsEnvironmentName string

@description('Name for the Container Registry')
param containerRegistryName string

@description('Subnet resource ID for VNet integration')
param subnetResourceId string = ''

@description('Whether to use private ingress')
param usePrivateIngress bool = false

@description('Container Registry SKU')
@allowed(['Basic', 'Standard', 'Premium'])
param registrySku string = 'Basic'

var hasVnet = !empty(subnetResourceId)

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerAppsEnvironmentName
  location: location
  tags: tags
  properties: {
    vnetConfiguration: hasVnet ? {
      infrastructureSubnetId: subnetResourceId
      internal: usePrivateIngress
    } : null
  }
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: containerRegistryName
  location: location
  tags: tags
  sku: { name: registrySku }
  properties: {
    adminUserEnabled: true
  }
}

param managedIdentityResourceId string

resource frontendApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ai-tour-frontend'
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentityResourceId}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 80
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: managedIdentityResourceId
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: '${containerRegistry.properties.loginServer}/ai-tour-frontend:latest'
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}


output environmentName string = containerAppsEnvironment.name
output environmentId string = containerAppsEnvironment.id
output defaultDomain string = containerAppsEnvironment.properties.defaultDomain
output registryName string = containerRegistry.name
output registryId string = containerRegistry.id
