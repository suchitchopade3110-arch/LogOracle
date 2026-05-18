#!/usr/bin/env bash
# scripts/tls_setup.sh
# Replaces self-signed certs with real TLS certificates.
#
# TWO OPTIONS depending on your deployment:
#
# Option A — You have a domain (recommended for demo judges):
#   Uses certbot (Let's Encrypt). Free, auto-renews.
#
# Option B — No domain (localhost/IP demo):
#   Generates a proper self-signed cert with correct SANs.
#   Browsers still warn, but curl -k and the app work correctly.
#
# Usage:
#   chmod +x scripts/tls_setup.sh
#   ./scripts/tls_setup.sh          # Option B (default, no domain needed)
#   DOMAIN=yourdomain.com ./scripts/tls_setup.sh   # Option A

set -euo pipefail

CERT_DIR="./infra/certs"
mkdir -p "$CERT_DIR"

DOMAIN="${DOMAIN:-}"

# ── OPTION A: Let's Encrypt (requires public domain + port 80 open) ────────
if [ -n "$DOMAIN" ]; then
  echo "🔒 Option A: Let's Encrypt for $DOMAIN"

  if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    sudo apt-get install -y certbot
  fi

  # Stop nginx temporarily for standalone challenge
  docker compose --env-file .env -f infra/docker-compose.yml stop nginx 2>/dev/null || true

  sudo certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email "admin@${DOMAIN}" \
    -d "$DOMAIN"

  # Copy to infra/certs (nginx reads from here)
  sudo cp "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" "$CERT_DIR/server.crt"
  sudo cp "/etc/letsencrypt/live/${DOMAIN}/privkey.pem"   "$CERT_DIR/server.key"
  sudo chown "$USER":"$USER" "$CERT_DIR/server.crt" "$CERT_DIR/server.key"

  docker compose --env-file .env -f infra/docker-compose.yml start nginx

  echo "✅ Let's Encrypt cert installed for $DOMAIN"
  echo "   Auto-renewal: sudo certbot renew --quiet (add to crontab)"

# ── OPTION B: Self-signed with correct SANs (demo / localhost) ────────────
else
  echo "🔒 Option B: Self-signed cert with SANs (localhost + 127.0.0.1)"

  # Get machine IP for SAN
  LOCAL_IP=$(hostname -I | awk '{print $1}')

  openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes \
    -keyout "$CERT_DIR/server.key" \
    -out    "$CERT_DIR/server.crt" \
    -subj   "/CN=logoracle-demo" \
    -addext "subjectAltName=DNS:localhost,DNS:logoracle.local,IP:127.0.0.1,IP:${LOCAL_IP}"

  chmod 600 "$CERT_DIR/server.key"

  echo "✅ Self-signed cert generated:"
  echo "   $CERT_DIR/server.crt  (valid 365 days)"
  echo "   $CERT_DIR/server.key"
  echo ""
  echo "   SANs: localhost, logoracle.local, 127.0.0.1, $LOCAL_IP"
  echo ""
  echo "   To trust in browser (Ubuntu):"
  echo "     sudo cp $CERT_DIR/server.crt /usr/local/share/ca-certificates/logoracle.crt"
  echo "     sudo update-ca-certificates"
  echo ""
  echo "   Restart nginx: docker compose --env-file .env -f infra/docker-compose.yml restart nginx"
fi
