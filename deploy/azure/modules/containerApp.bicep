// ==========================================================================
// Reusable Container App module — one instance per service.
// Handles ingress (external HTTP / internal HTTP / internal TCP / none),
// ACR pull via registry admin credentials, secrets, env vars and Azure Files mounts.
// ==========================================================================

@description('Container App name (also the in-environment hostname for service-to-service calls).')
param name string

param location string = resourceGroup().location

@description('Resource ID of the Container Apps managed environment.')
param environmentId string

@description('ACR login server, e.g. iiotacr123.azurecr.io')
param acrLoginServer string

@description('ACR admin username (used to pull images).')
param acrUsername string

@description('ACR admin password (used to pull images).')
@secure()
param acrPassword string

@description('Full image reference, e.g. iiotacr123.azurecr.io/ai-engine:latest')
param image string

@description('Ingress kind for this app.')
@allowed([
  'external-http'
  'internal-http'
  'internal-tcp'
  'none'
])
param ingressKind string = 'none'

@description('Container listening port. Ignored when ingressKind == none.')
param targetPort int = 80

param cpu string = '0.5'
param memory string = '1.0Gi'
param minReplicas int = 1
param maxReplicas int = 1

@description('Startup probe failure threshold (each attempt is ~10s apart). Raise for slow-starting apps like ai-engine that load ML models on boot.')
param startupFailureThreshold int = 6

@description('Plain (non-secret) environment variables: [{ name, value }].')
param envVars array = []

@description('Secret-backed env vars: [{ name (ENV name), secretRef }].')
param secretEnvVars array = []

@description('App secrets: [{ name, value }]. Referenced by secretEnvVars[].secretRef.')
param secrets array = []

@description('Azure Files volume mounts: [{ volumeName, storageName, mountPath }].')
param volumeMounts array = []

var hasIngress = ingressKind != 'none'

var ingressConfig = ingressKind == 'external-http' ? {
  external: true
  targetPort: targetPort
  transport: 'auto'
  allowInsecure: false
} : ingressKind == 'internal-http' ? {
  external: false
  targetPort: targetPort
  transport: 'auto'
  allowInsecure: false
} : ingressKind == 'internal-tcp' ? {
  external: false
  transport: 'tcp'
  targetPort: targetPort
  exposedPort: targetPort
} : null

var secretEnvList = [for s in secretEnvVars: {
  name: s.name
  secretRef: s.secretRef
}]

var containerEnv = concat(envVars, secretEnvList)

var volumes = [for v in volumeMounts: {
  name: v.volumeName
  storageType: 'AzureFile'
  storageName: v.storageName
}]

var containerVolumeMounts = [for v in volumeMounts: {
  volumeName: v.volumeName
  mountPath: v.mountPath
}]

// Append the ACR pull password as an app secret referenced by the registry config.
var allSecrets = concat(secrets, [
  {
    name: 'acr-pull-password'
    value: acrPassword
  }
])

// Lenient TCP startup probe so slow-booting apps (ai-engine loads an embedding
// model on first start) aren't killed before they bind their port. Once started,
// the platform leaves them alone (no aggressive liveness probe).
var probes = hasIngress ? [
  {
    type: 'Startup'
    tcpSocket: {
      port: targetPort
    }
    initialDelaySeconds: 5
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: startupFailureThreshold
  }
] : []

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: hasIngress ? ingressConfig : null
      secrets: allSecrets
      registries: [
        {
          server: acrLoginServer
          username: acrUsername
          passwordSecretRef: 'acr-pull-password'
        }
      ]
    }
    template: {
      containers: [
        {
          name: name
          image: image
          resources: {
            cpu: json(cpu)
            memory: memory
          }
          env: containerEnv
          volumeMounts: containerVolumeMounts
          probes: probes
        }
      ]
      volumes: volumes
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
      }
    }
  }
}

output fqdn string = hasIngress && ingressKind == 'external-http' ? app.properties.configuration.ingress.fqdn : ''
output appName string = app.name
