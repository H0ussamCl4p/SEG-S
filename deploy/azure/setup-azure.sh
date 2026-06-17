#!/usr/bin/env bash
# ==========================================================================
# One-shot Azure deployment for the IIoT Predictive Maintenance stack.
# Mirrors deploy/setup-vps.sh, but targets Azure Container Apps.
#
# Prereqs:
#   - Azure CLI (az) installed and `az login` done
#   - The containerapp extension (the script installs it if missing)
#   - Run from the repo root or anywhere; paths are resolved relative to this file
#
# Usage:
#   DEEPSEEK_API_KEY=sk-... \
#   POSTGRES_PASSWORD='S0me-Strong-Pass!' \
#   bash deploy/azure/setup-azure.sh
#
# Optional env overrides: RESOURCE_GROUP, LOCATION, NAME_PREFIX, IMAGE_TAG,
#   ROOT_DOMAIN, API_DOMAIN, AUTH_DOMAIN, JWT_SECRET_KEY
# ==========================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ---- Configuration ---------------------------------------------------------
RESOURCE_GROUP="${RESOURCE_GROUP:-iiot-rg}"
LOCATION="${LOCATION:-westeurope}"
NAME_PREFIX="${NAME_PREFIX:-iiot}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
ROOT_DOMAIN="${ROOT_DOMAIN:-eneguardian.app}"
API_DOMAIN="${API_DOMAIN:-api.eneguardian.app}"
AUTH_DOMAIN="${AUTH_DOMAIN:-auth.eneguardian.app}"

# ---- Secrets ---------------------------------------------------------------
: "${DEEPSEEK_API_KEY:?Set DEEPSEEK_API_KEY (your DeepSeek API key)}"
: "${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD (strong PostgreSQL admin password)}"
# JWT secret: generate one if not supplied.
if [[ -z "${JWT_SECRET_KEY:-}" ]]; then
  JWT_SECRET_KEY="$(openssl rand -hex 32)"
  echo "Generated JWT_SECRET_KEY automatically."
fi

# ---- Prerequisites ---------------------------------------------------------
command -v az >/dev/null 2>&1 || { echo "ERROR: Azure CLI (az) not found. Install it first."; exit 1; }
echo "=== [0/5] Ensuring az containerapp extension + providers ==="
az extension add --name containerapp --upgrade --only-show-errors >/dev/null
az provider register --namespace Microsoft.App --wait
az provider register --namespace Microsoft.OperationalInsights --wait
az provider register --namespace Microsoft.DBforPostgreSQL --wait

echo "=== [1/5] Resource group ($RESOURCE_GROUP @ $LOCATION) ==="
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --only-show-errors >/dev/null

echo "=== [2/5] Container Registry ==="
az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --name registry \
  --template-file "$SCRIPT_DIR/registry.bicep" \
  --parameters namePrefix="$NAME_PREFIX" \
  --only-show-errors >/dev/null

ACR_NAME="$(az deployment group show -g "$RESOURCE_GROUP" -n registry --query properties.outputs.acrName.value -o tsv)"
ACR_LOGIN_SERVER="$(az deployment group show -g "$RESOURCE_GROUP" -n registry --query properties.outputs.acrLoginServer.value -o tsv)"
echo "ACR: $ACR_LOGIN_SERVER"

echo "=== [3/5] Building images in ACR (no local Docker needed) ==="
# Frontend bakes NEXT_PUBLIC_* at build time -> pass the production domains.
build() {
  local image="$1"; local context="$2"; shift 2
  echo "  -> $image"
  az acr build --registry "$ACR_NAME" --image "$image:$IMAGE_TAG" "$@" "$context" --only-show-errors >/dev/null
}

build auth-service "$REPO_ROOT/services/auth-service"
build ai-engine    "$REPO_ROOT/services/ai-engine"
build simulator    "$REPO_ROOT/services/simulator"
build mosquitto    "$REPO_ROOT/infrastructure/mosquitto"
build web-frontend "$REPO_ROOT/services/web-frontend" \
  --build-arg "NEXT_PUBLIC_API_URL=https://$API_DOMAIN" \
  --build-arg "NEXT_PUBLIC_AUTH_URL=https://$AUTH_DOMAIN"

echo "=== [4/5] Deploying stack (main.bicep) ==="
az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --name main \
  --template-file "$SCRIPT_DIR/main.bicep" \
  --parameters "$SCRIPT_DIR/main.parameters.json" \
  --parameters \
      namePrefix="$NAME_PREFIX" \
      acrName="$ACR_NAME" \
      imageTag="$IMAGE_TAG" \
      rootDomain="$ROOT_DOMAIN" \
      apiDomain="$API_DOMAIN" \
      authDomain="$AUTH_DOMAIN" \
      pgAdminPassword="$POSTGRES_PASSWORD" \
      jwtSecretKey="$JWT_SECRET_KEY" \
      deepseekApiKey="$DEEPSEEK_API_KEY" \
  --only-show-errors >/dev/null

echo "=== [5/5] Done. Default Container Apps URLs ==="
FRONTEND_FQDN="$(az deployment group show -g "$RESOURCE_GROUP" -n main --query properties.outputs.frontendFqdn.value -o tsv)"
API_FQDN="$(az deployment group show -g "$RESOURCE_GROUP" -n main --query properties.outputs.apiFqdn.value -o tsv)"
AUTH_FQDN="$(az deployment group show -g "$RESOURCE_GROUP" -n main --query properties.outputs.authFqdn.value -o tsv)"

cat <<EOF

  Frontend  -> https://$FRONTEND_FQDN
  AI Engine -> https://$API_FQDN/api/docs
  Auth      -> https://$AUTH_FQDN/auth/docs

To use your custom domains ($ROOT_DOMAIN, $API_DOMAIN, $AUTH_DOMAIN):
  1. Create these DNS records at your registrar:
       CNAME  $ROOT_DOMAIN            -> $FRONTEND_FQDN
       CNAME  $API_DOMAIN             -> $API_FQDN
       CNAME  $AUTH_DOMAIN            -> $AUTH_FQDN
       TXT    asuid.$ROOT_DOMAIN      -> <domain verification id, see below>
       TXT    asuid.$API_DOMAIN       -> <domain verification id>
       TXT    asuid.$AUTH_DOMAIN      -> <domain verification id>
     Get each verification id with:
       az containerapp show -g $RESOURCE_GROUP -n web-frontend --query properties.customDomainVerificationId -o tsv
  2. After DNS propagates, bind + issue managed certs:
       bash deploy/azure/bind-domains.sh
EOF
