#!/bin/bash

echo "🛑 Stopping LogOracle..."

BACKEND_DIR="$(dirname "$0")/logoracle-backend"
export DOCKER_HOST=unix:///var/run/docker.sock

# Kill backend
if [ -f /tmp/logoracle-api.pid ]; then
    kill $(cat /tmp/logoracle-api.pid) 2>/dev/null
    rm /tmp/logoracle-api.pid
    echo "  ✓ Backend stopped"
fi

# Kill any remaining uvicorn
pkill -f "uvicorn main:app" 2>/dev/null || true

# Stop docker services
cd "$BACKEND_DIR/infra/monitoring"
sudo docker compose down 2>/dev/null
echo "  ✓ Prometheus + Grafana stopped"

cd "$BACKEND_DIR/infra/keycloak"
sudo docker compose down 2>/dev/null
echo "  ✓ Keycloak stopped"

echo "  �� LogOracle stopped."
