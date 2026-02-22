targetScope = 'resourceGroup'

@minLength(1)
@maxLength(64)
@description('Name used to generate a short unique hash for each resource')
param name string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Flag to enable virtual network for private networking')
param useVnet bool = false

@description('Enable private ingress for container apps')
param usePrivateIngress bool = false

var resourceToken = toLower(uniqueString(subscription().id, name, location))
var tags = { 'azd-env-name': name }
var prefix = '${name}-${resourceToken}'

var names = {
  keyVault: '${take(replace(prefix, '-', ''), 20)}kv'
  containerAppsEnv: '${prefix}-containerapps-env'
  containerRegistry: '${take(replace(prefix, '-', ''), 42)}registry'
  mcpServer: '${name}-mcp-server'
  Identity: '${prefix}-id-mcp-server'
  conciergeApi: '${name}-concierge-api'
  conciergeApiIdentity: '${prefix}-id-concierge-api'
  nsg: '${prefix}-container-apps-nsg'
  vnet: '${prefix}-vnet'
}

resource Identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: names.Identity
  location: location
  tags: tags
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: names.containerRegistry
}

resource acrPushRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, Identity.name, 'acrp')
  scope: containerRegistry
  properties: {
    principalId: Identity.properties.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPush
    principalType: 'ServicePrincipal'
  }
}

module keyVault 'br/public:avm/res/key-vault/vault:0.6.1' = {
  name: 'keyvault'
  params: {
    name: names.keyVault
    location: location
    tags: tags
    enableRbacAuthorization: true
    sku: 'standard'
  }
}

module aiProject 'ai-project.bicep' = {
  name: 'ai-project'
  params: {
    location: location
    tags: tags
  }
}

module containerAppsNSG 'br/public:avm/res/network/network-security-group:0.5.1' = if (useVnet) {
  name: 'containerAppsNSG'
  params: {
    name: names.nsg
    location: location
    tags: tags
    securityRules: usePrivateIngress ? [] : [
      {
        name: 'AllowHttpsInbound'
        properties: {
          protocol: 'Tcp'
          sourcePortRange: '*'
          sourceAddressPrefix: 'Internet'
          destinationPortRange: '443'
          destinationAddressPrefix: '*'
          access: 'Allow'
          priority: 100
          direction: 'Inbound'
      managedIdentityResourceId: Identity.id
        }
      }
    ]
  }
}

module virtualNetwork 'br/public:avm/res/network/virtual-network:0.6.1' = if (useVnet) {
  name: 'vnet'
  params: {
    name: names.vnet
    location: location
    tags: tags
    addressPrefixes: ['10.0.0.0/16']
    subnets: [
      {
        name: 'container-apps-subnet'
        addressPrefix: '10.0.0.0/21'
        networkSecurityGroupResourceId: containerAppsNSG!.outputs.resourceId
        delegation: 'Microsoft.App/environments'
      }
      {
        name: 'private-endpoints-subnet'
        addressPrefix: '10.0.8.0/24'
        privateEndpointNetworkPolicies: 'Enabled'
      }
    ]
  }
}

module containerAppsInfra 'container-apps.bicep' = {
  name: 'aitour-agent'
  params: {
    containerAppsEnvironmentName: names.containerAppsEnv
    containerRegistryName: names.containerRegistry
    location: location
    tags: tags
    subnetResourceId: useVnet ? virtualNetwork!.outputs.subnetResourceIds[0] : ''
    usePrivateIngress: usePrivateIngress
    registrySku: 'Standard'
    managedIdentityResourceId: Identity.id
  }
}

output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = resourceGroup().name
output AZURE_CONTAINER_ENVIRONMENT_NAME string = containerAppsInfra.outputs.environmentName
output AZURE_CONTAINER_REGISTRY_NAME string = containerAppsInfra.outputs.registryName
output AZURE_KEY_VAULT_NAME string = keyVault.outputs.name
output AZURE_AI_FOUNDRY_ENDPOINT string = aiProject.outputs.endpoint
output AZURE_AI_FOUNDRY_PROJECT string = aiProject.outputs.projectName
output AZURE_AI_FOUNDRY_NAME string = aiProject.outputs.foundryName
