// ==========================================================================
// Phase 2 — Full IIoT stack on Azure Container Apps
// Provisions: Log Analytics, Storage + file shares, PostgreSQL Flexible Server,
// a user-assigned identity (AcrPull), the Container Apps environment, and the
// six container apps. References the ACR created by registry.bicep.
//
// Run AFTER registry.bicep + `az acr build` so images already exist.
// ==========================================================================

@description('Short project prefix used to derive resource names.')
param namePrefix string = 'iiot'

param location string = resourceGroup().location

@description('Name of the existing ACR (output of registry.bicep).')
param acrName string

@description('Image tag to deploy for all services.')
param imageTag string = 'latest'

// ---- Public domains (frontend bakes these into the browser bundle) ----------
@description('Root domain for the dashboard.')
param rootDomain string = 'eneguardian.app'
param apiDomain string = 'api.eneguardian.app'
param authDomain string = 'auth.eneguardian.app'

// ---- Secrets ---------------------------------------------------------------
@secure()
param pgAdminPassword string
@secure()
param jwtSecretKey string
@secure()
param deepseekApiKey string

param pgAdminLogin string = 'iiot_admin'
param pgDatabaseName string = 'iiot_users'
param accessTokenExpireMinutes string = '60'
param llmModel string = 'deepseek-chat'
param llmApiBase string = 'https://api.deepseek.com'
param influxDatabase string = 'factory_data'

// ==========================================================================
// Existing registry
// ==========================================================================
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: acrName
}
var acrLoginServer = acr.properties.loginServer

// ==========================================================================
// Observability
// ==========================================================================
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${namePrefix}-logs'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

// ==========================================================================
// Storage account + file shares (persistence for stateful apps)
// ==========================================================================
var storageAccountName = toLower('${namePrefix}st${uniqueString(resourceGroup().id)}')

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

resource fileService 'Microsoft.Storage/storageAccounts/fileServices@2023-01-01' = {
  parent: storage
  name: 'default'
}

var shareNames = [
  'influx-data'
  'aiengine-data'
]

resource shares 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-01-01' = [for s in shareNames: {
  parent: fileService
  name: s
  properties: {
    shareQuota: 50
  }
}]

// ==========================================================================
// PostgreSQL Flexible Server (managed) — replaces the postgres container
// ==========================================================================
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' = {
  name: '${namePrefix}-pg-${uniqueString(resourceGroup().id)}'
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    administratorLogin: pgAdminLogin
    administratorLoginPassword: pgAdminPassword
    storage: { storageSizeGB: 32 }
    backup: { backupRetentionDays: 7, geoRedundantBackup: 'Disabled' }
    highAvailability: { mode: 'Disabled' }
    authConfig: { passwordAuth: 'Enabled', activeDirectoryAuth: 'Disabled' }
  }
}

resource pgDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-06-01-preview' = {
  parent: postgres
  name: pgDatabaseName
}

// Allow other Azure services (the Container Apps egress) to reach the server.
resource pgFirewallAzure 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-06-01-preview' = {
  parent: postgres
  name: 'AllowAllAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

var databaseUrl = 'postgresql://${pgAdminLogin}:${pgAdminPassword}@${postgres.properties.fullyQualifiedDomainName}:5432/${pgDatabaseName}?sslmode=require'

// ==========================================================================
// Managed identity for ACR pulls
// ==========================================================================
resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${namePrefix}-pull-identity'
  location: location
}

// AcrPull role
resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: acr
  name: guid(acr.id, uami.id, 'AcrPull')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: uami.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ==========================================================================
// Container Apps environment + Azure Files storages
// ==========================================================================
resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${namePrefix}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource envStorages 'Microsoft.App/managedEnvironments/storages@2024-03-01' = [for s in shareNames: {
  parent: env
  name: s
  properties: {
    azureFile: {
      accountName: storage.name
      accountKey: storage.listKeys().keys[0].value
      shareName: s
      accessMode: 'ReadWrite'
    }
  }
}]

// ==========================================================================
// Image references
// ==========================================================================
var images = {
  authService: '${acrLoginServer}/auth-service:${imageTag}'
  aiEngine: '${acrLoginServer}/ai-engine:${imageTag}'
  simulator: '${acrLoginServer}/simulator:${imageTag}'
  webFrontend: '${acrLoginServer}/web-frontend:${imageTag}'
  mosquitto: '${acrLoginServer}/mosquitto:${imageTag}'
}

// ==========================================================================
// Stateful infrastructure apps (single replica, file-backed)
// ==========================================================================

// MQTT broker — internal TCP, reachable in-env at host "mosquitto:1883"
module mosquitto 'modules/containerApp.bicep' = {
  name: 'mosquitto'
  params: {
    location: location
    environmentId: env.id
    identityId: uami.id
    acrLoginServer: acrLoginServer
    name: 'mosquitto'
    // Config baked into the image (infrastructure/mosquitto/Dockerfile).
    image: images.mosquitto
    ingressKind: 'internal-tcp'
    targetPort: 1883
    cpu: '0.25'
    memory: '0.5Gi'
    minReplicas: 1
    maxReplicas: 1
  }
  dependsOn: [ acrPull ]
}

// Time-series DB — internal HTTP, reachable in-env at host "influxdb:8086"
module influxdb 'modules/containerApp.bicep' = {
  name: 'influxdb'
  params: {
    location: location
    environmentId: env.id
    identityId: uami.id
    acrLoginServer: acrLoginServer
    name: 'influxdb'
    image: 'influxdb:1.8'
    // TCP ingress preserves the native 8086 port for the InfluxDB client
    // (HTTP ingress would only expose port 80 in-environment).
    ingressKind: 'internal-tcp'
    targetPort: 8086
    cpu: '0.5'
    memory: '1.0Gi'
    minReplicas: 1
    maxReplicas: 1
    envVars: [
      { name: 'INFLUXDB_DB', value: influxDatabase }
      { name: 'INFLUXDB_HTTP_AUTH_ENABLED', value: 'false' }
    ]
    volumeMounts: [
      { volumeName: 'influx-data', storageName: 'influx-data', mountPath: '/var/lib/influxdb' }
    ]
  }
  dependsOn: [ envStorages, acrPull ]
}

// ==========================================================================
// Application services
// ==========================================================================

module authService 'modules/containerApp.bicep' = {
  name: 'auth-service'
  params: {
    location: location
    environmentId: env.id
    identityId: uami.id
    acrLoginServer: acrLoginServer
    name: 'auth-service'
    image: images.authService
    ingressKind: 'external-http'
    targetPort: 8001
    cpu: '0.5'
    memory: '1.0Gi'
    minReplicas: 1
    maxReplicas: 3
    envVars: [
      { name: 'ACCESS_TOKEN_EXPIRE_MINUTES', value: accessTokenExpireMinutes }
    ]
    secretEnvVars: [
      { name: 'DATABASE_URL', secretRef: 'database-url' }
      { name: 'JWT_SECRET_KEY', secretRef: 'jwt-secret' }
    ]
    secrets: [
      { name: 'database-url', value: databaseUrl }
      { name: 'jwt-secret', value: jwtSecretKey }
    ]
  }
  dependsOn: [ acrPull, pgDatabase ]
}

module aiEngine 'modules/containerApp.bicep' = {
  name: 'ai-engine'
  params: {
    location: location
    environmentId: env.id
    identityId: uami.id
    acrLoginServer: acrLoginServer
    name: 'ai-engine'
    image: images.aiEngine
    ingressKind: 'external-http'
    targetPort: 8000
    cpu: '1.0'
    memory: '2.0Gi'
    // Single replica: it holds the MQTT subscription and ingests into InfluxDB.
    minReplicas: 1
    maxReplicas: 1
    envVars: [
      { name: 'INFLUX_HOST', value: 'influxdb' }
      { name: 'INFLUX_PORT', value: '8086' }
      { name: 'INFLUX_DB', value: influxDatabase }
      { name: 'MQTT_BROKER', value: 'mosquitto' }
      { name: 'MQTT_PORT', value: '1883' }
      { name: 'PYTHONUNBUFFERED', value: '1' }
      { name: 'ACCESS_TOKEN_EXPIRE_MINUTES', value: accessTokenExpireMinutes }
      { name: 'LLM_API_BASE', value: llmApiBase }
      { name: 'LLM_MODEL', value: llmModel }
      // Persist the Chroma vector index on the mounted share (not the baked /app/data).
      { name: 'CHROMA_PERSIST_DIR', value: '/app/persist/chroma' }
    ]
    secretEnvVars: [
      { name: 'JWT_SECRET_KEY', secretRef: 'jwt-secret' }
      { name: 'LLM_API_KEY', secretRef: 'deepseek-key' }
    ]
    secrets: [
      { name: 'jwt-secret', value: jwtSecretKey }
      { name: 'deepseek-key', value: deepseekApiKey }
    ]
    volumeMounts: [
      { volumeName: 'aiengine-data', storageName: 'aiengine-data', mountPath: '/app/persist' }
    ]
  }
  dependsOn: [ acrPull, influxdb, mosquitto ]
}

module simulator 'modules/containerApp.bicep' = {
  name: 'simulator'
  params: {
    location: location
    environmentId: env.id
    identityId: uami.id
    acrLoginServer: acrLoginServer
    name: 'simulator'
    image: images.simulator
    ingressKind: 'none'
    cpu: '0.25'
    memory: '0.5Gi'
    minReplicas: 1
    maxReplicas: 1
    envVars: [
      { name: 'MQTT_BROKER', value: 'mosquitto' }
      { name: 'MQTT_PORT', value: '1883' }
      { name: 'SIMULATION_INTERVAL', value: '1' }
      { name: 'PYTHONUNBUFFERED', value: '1' }
    ]
  }
  dependsOn: [ acrPull, mosquitto ]
}

module webFrontend 'modules/containerApp.bicep' = {
  name: 'web-frontend'
  params: {
    location: location
    environmentId: env.id
    identityId: uami.id
    acrLoginServer: acrLoginServer
    name: 'web-frontend'
    image: images.webFrontend
    ingressKind: 'external-http'
    targetPort: 3000
    cpu: '0.5'
    memory: '1.0Gi'
    minReplicas: 1
    maxReplicas: 3
    envVars: [
      { name: 'NEXT_PUBLIC_API_URL', value: 'https://${apiDomain}' }
      { name: 'NEXT_PUBLIC_AUTH_URL', value: 'https://${authDomain}' }
      { name: 'AI_ENGINE_URL', value: 'http://ai-engine' }
      { name: 'AUTH_SERVICE_URL', value: 'http://auth-service' }
    ]
  }
  dependsOn: [ acrPull, aiEngine, authService ]
}

// ==========================================================================
// Outputs — FQDNs to point DNS at
// ==========================================================================
output frontendFqdn string = webFrontend.outputs.fqdn
output apiFqdn string = aiEngine.outputs.fqdn
output authFqdn string = authService.outputs.fqdn
output acrLoginServerOut string = acrLoginServer
output postgresFqdn string = postgres.properties.fullyQualifiedDomainName
output rootDomainOut string = rootDomain
