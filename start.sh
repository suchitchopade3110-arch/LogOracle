#!/bin/bash
set -e

echo "🔮 Starting LogOracle..."

# ── Colors ────────────────────────────────────────
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

BACKEND_DIR="$(dirname "$0")/logoracle-backend"
ROOT_DIR="$(dirname "$0")"

# ── Step 1: Docker ────────────────────────────────
echo -e "${CYAN}[1/4] Starting Docker services...${NC}"
sudo systemctl start docker
export DOCKER_HOST=unix:///var/run/docker.sock

# Keycloak
cd "$BACKEND_DIR/infra/keycloak"
sudo docker compose up -d
echo -e "${GREEN}  ✓ Keycloak started (:8080)${NC}"

# Prometheus + Grafana
cd "$BACKEND_DIR/infra/monitoring"
sudo docker compose up -d
echo -e "${GREEN}  ✓ Prometheus started (:9090)${NC}"
echo -e "${GREEN}  ✓ Grafana started (:3001)${NC}"

# ── Step 2: Backend ───────────────────────────────
echo -e "${CYAN}[2/4] Starting FastAPI backend...${NC}"
cd "$BACKEND_DIR"
source venv/bin/activate
unset GROQ_API_KEY
export DOCKER_HOST=unix:///var/run/docker.sock

nohup uvicorn main:app --host 0.0.0.0 --port 8001 > /tmp/logoracle-api.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > /tmp/logoracle-api.pid

sleep 3

# Health check
if curl -s http://localhost:8001/health > /dev/null; then
    echo -e "${GREEN}  ✓ Backend started (:8001) PID=$BACKEND_PID${NC}"
else
    echo -e "${RED}  ✗ Backend failed to start. Check /tmp/logoracle-api.log${NC}"
    exit 1
fi

# ── Step 3: Set API key ───────────────────────────
echo -e "${CYAN}[3/4] Configuring environment...${NC}"
export LOGORACLE_API_KEY=$(grep "^API_KEY=" "$BACKEND_DIR/.env" | cut -d= -f2)
if [ -z "$LOGORACLE_API_KEY" ]; then
    export LOGORACLE_API_KEY="logoracle-dev-key-2026"
fi
echo -e "${GREEN}  ✓ API key set${NC}"

# ── Step 4: Summary ───────────────────────────────
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  🔮 LogOracle is running!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "  Backend    → http://localhost:8001"
echo -e "  Prometheus → http://localhost:9090"
echo -e "  Grafana    → http://localhost:3001"
echo -e "  Keycloak   → http://localhost:8080"
echo -e "  API Docs   → http://localhost:8001/docs"
echo ""
echo -e "${CYAN}  To launch Terminal TUI:${NC}"
echo -e "  cd $ROOT_DIR"
echo -e "  source .venv/bin/activate"
echo -e "  export LOGORACLE_API_KEY=$LOGORACLE_API_KEY"
echo -e "  python logoracle_cli.py --watch /var/log/syslog"
echo ""
echo -e "${CYAN}  To stop everything:${NC}"
echo -e "  bash stop.sh"
echo -e "${GREEN}════════════════════════════════════════${NC}"
