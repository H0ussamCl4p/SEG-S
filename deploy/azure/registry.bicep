// ==========================================================================
// Phase 1 — Azure Container Registry
// Deployed BEFORE building images so `az acr build` has somewhere to push.
// main.bicep later references this registry as `existing`.
// ==========================================================================

@description('Short project prefix used to derive resource names.')
param namePrefix string = 'iiot'

@description('Azure region for the registry.')
param location string = resourceGroup().location

// ACR names are global, alphanumeric only, 5-50 chars.
var acrName = toLower('${namePrefix}acr${uniqueString(resourceGroup().id)}')

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    // Admin user enabled so Container Apps can pull with registry credentials
    // (avoids needing an AcrPull role assignment, which can be restricted on
    // Azure for Students / personal-account subscriptions).
    adminUserEnabled: true
  }
}

output acrName string = acr.name
output acrLoginServer string = acr.properties.loginServer
