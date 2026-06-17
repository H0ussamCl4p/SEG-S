# Azure deployment (Container Apps)

Re-hosts the IIoT Predictive Maintenance stack on **Azure Container Apps (ACA)**.
Replaces the single-VPS + nginx + certbot setup. The chatbot LLM runs on the
**DeepSeek API** (OpenAI-compatible), so no GPU is required.

## Architecture

| Component | Azure resource | Ingress |
|-----------|----------------|---------|
| web-frontend (Next.js) | Container App | external → `eneguardian.app` |
| ai-engine (FastAPI) | Container App | external → `api.eneguardian.app` |
| auth-service (FastAPI) | Container App | external → `auth.eneguardian.app` |
| influxdb 1.8 | Container App + Azure Files | internal (`influxdb:8086`) |
| mosquitto (MQTT) | Container App (config baked in image) | internal TCP (`mosquitto:1883`) |
| simulator | Container App | none |
| Users DB | Azure Database for PostgreSQL Flexible Server | private |
| Images | Azure Container Registry | — |
| Logs | Log Analytics workspace | — |

Each external app gets ACA-managed TLS on its own `*.azurecontainerapps.io` FQDN;
custom domains are bound afterwards with managed certificates. No nginx.

## Files
- `registry.bicep` — ACR (deployed first so `az acr build` has a target).
- `main.bicep` — everything else; references the ACR as existing.
- `modules/containerApp.bicep` — reusable Container App (ingress/secrets/volumes).
- `main.parameters.json` — non-secret defaults.
- `setup-azure.sh` — one-shot: RG → ACR → build images → deploy stack.
- `bind-domains.sh` — bind custom domains + managed certs (after DNS).

## Prerequisites
- Azure CLI (`az`) + `az login`
- A DeepSeek API key
- (For custom domains) control of the `eneguardian.app` DNS zone
- **Run `setup-azure.sh` as a subscription Owner or User Access Administrator** —
  `main.bicep` creates an `AcrPull` role assignment for the pull identity, which
  requires `Microsoft.Authorization/roleAssignments/write`. (The CI workflow only
  builds images and updates apps, so it just needs Contributor on the resource group.)

## Deploy

```bash
# from the repo root
DEEPSEEK_API_KEY=sk-xxxxxxxx \
POSTGRES_PASSWORD='Strong-Passw0rd!' \
bash deploy/azure/setup-azure.sh
```

Optional overrides (env vars): `RESOURCE_GROUP`, `LOCATION` (default `westeurope`),
`NAME_PREFIX`, `IMAGE_TAG`, `ROOT_DOMAIN`, `API_DOMAIN`, `AUTH_DOMAIN`,
`JWT_SECRET_KEY` (auto-generated if unset).

The script prints the live `*.azurecontainerapps.io` URLs at the end — the stack
is usable immediately on those.

## Custom domains

1. Get the verification id (same for all apps in the env):
   ```bash
   az containerapp show -g iiot-rg -n web-frontend \
     --query properties.customDomainVerificationId -o tsv
   ```
2. Create DNS records:
   ```
   CNAME  eneguardian.app          -> <frontend FQDN>
   CNAME  api.eneguardian.app      -> <ai-engine FQDN>
   CNAME  auth.eneguardian.app     -> <auth-service FQDN>
   TXT    asuid.eneguardian.app    -> <verification id>
   TXT    asuid.api.eneguardian.app  -> <verification id>
   TXT    asuid.auth.eneguardian.app -> <verification id>
   ```
   (Apex `eneguardian.app` as CNAME needs a provider with CNAME-flattening/ALIAS,
   e.g. Cloudflare. Otherwise use `www` + a redirect, or an A record to the ACA
   static inbound IP.)
3. Bind + issue certs once DNS propagates:
   ```bash
   RESOURCE_GROUP=iiot-rg bash deploy/azure/bind-domains.sh
   ```

## CI/CD

`.github/workflows/azure-deploy.yml` builds images in ACR and rolls new revisions
on push to `main`. Configure:

- **Secrets:** `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`
  (federated OIDC app registration with Contributor on the resource group).
- **Variables:** `ACR_NAME`, `RESOURCE_GROUP`, `API_DOMAIN`, `AUTH_DOMAIN`.

## Notes / cost
- PostgreSQL is `Standard_B1ms` Burstable; InfluxDB runs as a single-replica
  Container App on a 50 GiB Azure Files share. `ai-engine`, `mosquitto`,
  `influxdb`, `simulator` are pinned to 1 replica (stateful / single-consumer).
- DeepSeek is billed per token by DeepSeek, not Azure.
- To tear everything down: `az group delete -n iiot-rg --yes --no-wait`.

## Smoke test
```bash
curl https://<auth FQDN>/auth/docs        # 200
curl https://<api FQDN>/api/docs          # 200
curl https://<api FQDN>/api/live          # telemetry JSON (simulator→mqtt→influx)
# open https://<frontend FQDN> and the chatbot page
```
