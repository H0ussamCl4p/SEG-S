#!/usr/bin/env bash
# ==========================================================================
# Bind custom domains + issue ACA managed TLS certificates.
# Run AFTER setup-azure.sh and AFTER the CNAME + asuid TXT DNS records exist
# and have propagated. Safe to re-run.
#
# Usage:
#   RESOURCE_GROUP=iiot-rg bash deploy/azure/bind-domains.sh
# ==========================================================================
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-iiot-rg}"
NAME_PREFIX="${NAME_PREFIX:-iiot}"
ENVIRONMENT="${ENVIRONMENT:-${NAME_PREFIX}-env}"
ROOT_DOMAIN="${ROOT_DOMAIN:-eneguardian.app}"
API_DOMAIN="${API_DOMAIN:-api.eneguardian.app}"
AUTH_DOMAIN="${AUTH_DOMAIN:-auth.eneguardian.app}"

command -v az >/dev/null 2>&1 || { echo "ERROR: Azure CLI (az) not found."; exit 1; }

# app:hostname pairs
bind() {
  local app="$1"; local host="$2"
  echo "=== Binding $host -> $app (managed cert) ==="
  # add hostname is idempotent enough; ignore if it already exists
  az containerapp hostname add -g "$RESOURCE_GROUP" -n "$app" --hostname "$host" --only-show-errors >/dev/null 2>&1 || true
  # bind + auto-create a managed certificate via CNAME validation
  az containerapp hostname bind \
    -g "$RESOURCE_GROUP" -n "$app" \
    --hostname "$host" \
    --environment "$ENVIRONMENT" \
    --validation-method CNAME \
    --only-show-errors
}

bind web-frontend "$ROOT_DOMAIN"
bind ai-engine    "$API_DOMAIN"
bind auth-service "$AUTH_DOMAIN"

echo ""
echo "Done. It can take a few minutes for managed certificates to be issued."
echo "Verify: az containerapp hostname list -g $RESOURCE_GROUP -n web-frontend -o table"
