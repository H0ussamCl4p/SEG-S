#!/bin/bash
# Run this script on the VPS as ubuntu user:
#   bash deploy/setup-vps.sh
set -euo pipefail

REPO_DIR="/home/ubuntu/iiot-predictive-maintenance"
ROOT_DOMAIN="eneguardian.app"
FRONTEND_DOMAIN="$ROOT_DOMAIN"
FRONTEND_WWW_DOMAIN="www.$ROOT_DOMAIN"
API_DOMAIN="api.$ROOT_DOMAIN"
AUTH_DOMAIN="auth.$ROOT_DOMAIN"

# Email used for Let's Encrypt registration.
# You can override it per-run:
#   LETSENCRYPT_EMAIL=you@domain.com bash deploy/setup-vps.sh
LETSENCRYPT_EMAIL="${LETSENCRYPT_EMAIL:-choubikhoussam@gmail.com}"

echo "=== [1/7] Installing Docker ==="
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker ubuntu
    echo "Docker installed. NOTE: log out and back in for group change to take effect if needed."
else
    echo "Docker already installed."
fi

echo "=== [2/7] Installing Nginx + Certbot ==="
sudo apt-get update -qq
sudo apt-get install -y nginx certbot ufw

echo "=== [3/7] Opening firewall ports ==="
sudo ufw allow 22/tcp   comment 'SSH'
sudo ufw allow 80/tcp   comment 'HTTP'
sudo ufw allow 443/tcp  comment 'HTTPS'
sudo ufw --force enable
echo "Firewall rules applied (22, 80, 443 open)."

echo "=== [4/7] Configuring Nginx (HTTP-only for ACME) ==="
sudo mkdir -p /var/www/certbot
sudo cp "$REPO_DIR/deploy/nginx.http.conf" /etc/nginx/nginx.conf
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

echo "=== [5/7] Issuing Let's Encrypt certificate ==="

sudo certbot certonly \
    --webroot -w /var/www/certbot \
    -d "$FRONTEND_DOMAIN" -d "$FRONTEND_WWW_DOMAIN" -d "$API_DOMAIN" -d "$AUTH_DOMAIN" \
    --email "$LETSENCRYPT_EMAIL" \
    --agree-tos --no-eff-email --non-interactive

echo "Switching Nginx to HTTPS reverse-proxy config..."
sudo cp "$REPO_DIR/deploy/nginx.conf" /etc/nginx/nginx.conf
sudo nginx -t
sudo systemctl restart nginx

echo "=== [6/7] Setting up environment file ==="
ENV_FILE="$REPO_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    cp "$REPO_DIR/deploy/.env.production" "$ENV_FILE"

    # Generate a strong JWT secret automatically
    JWT_SECRET=$(openssl rand -hex 32)
    sed -i "s|CHANGE_ME_run_openssl_rand_hex_32|$JWT_SECRET|" "$ENV_FILE"

    echo ""
    echo "  .env created. Generated JWT_SECRET_KEY automatically."
    echo "  Review $ENV_FILE and set PINECONE_API_KEY / OPENROUTER_API_KEY if needed."
else
    echo "  .env already exists, skipping."
fi

echo "=== [7/7] Starting Docker Compose stack ==="
cd "$REPO_DIR"
docker compose \
    -f docker-compose.yml \
    -f docker-compose.prod.yml \
    --env-file .env \
    up -d --build

echo ""
echo "=== Done! ==="
echo "Frontend  -> https://$FRONTEND_DOMAIN"
echo "AI Engine -> https://$API_DOMAIN/api/docs"
echo "Auth      -> https://$AUTH_DOMAIN/auth/docs"
echo ""
echo "Check service health:"
echo "  docker compose ps"
echo "  docker compose logs -f"
