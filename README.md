<div align="center">
  <img src="logo.png" alt="LogOracle" width="180"/>
</div>

# 🔮 LogOracle

> **First AI debugging platform with hallucinated dependency protection.**
> **The most trustworthy AI-native debugging and security copilot for developers.**

LogOracle watches your logs, reads your code, hunts supply-chain threats, builds a causal incident graph, and explains every conclusion with evidence — autonomously, before your users notice anything is wrong.

No more digging through 10,000 log lines at 3am. No more "works on my machine." No more security vulnerabilities shipping to production.

**LogOracle catches it first. Right in your terminal and your editor.**

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![GROQ](https://img.shields.io/badge/GROQ-LLaMA_3.1--8B-orange)](https://groq.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)](https://redis.io)
[![Vault](https://img.shields.io/badge/HashiCorp_Vault-black?logo=vault)](https://vaultproject.io)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?logo=prometheus&logoColor=white)](https://prometheus.io)
[![Grafana](https://img.shields.io/badge/Grafana-F46800?logo=grafana&logoColor=white)](https://grafana.com)
[![Keycloak](https://img.shields.io/badge/Keycloak-4D4D4D?logo=keycloak)](https://keycloak.org)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## 🧠 What Makes LogOracle Different

| Capability | LogOracle | Traditional Tools |
|---|---|---|
| Autonomous log monitoring | ✅ Zero config | ❌ Manual setup |
| Root-cause causal chaining | ✅ Full chain | ❌ Single alert |
| Supply-chain hallucination detection | ✅ Built-in | ❌ Not supported |
| 3-pass code intelligence (AST + LLM + OWASP) | ✅ All three | ❌ Partial |
| Agentic AI loop (6-step autonomous reasoning) | ✅ Built-in | ❌ Not supported |
| Self-heal relay (remote command execution) | ✅ Whitelisted | ❌ Not supported |
| Developer growth + quiz/XP system | ✅ Built-in | ❌ Not supported |
| Works in VS Code and terminal | ✅ Both surfaces | ❌ One surface |
| Hallucinated dependency detection | ✅ Industry first | ❌ Not supported |
| Self-monitoring (Prometheus + Grafana) | ✅ Built-in | ⚠️ Extra setup |

---

## 🤖 The Six Agents

The moment LogOracle starts, six agents activate in the background — no user action required.

| Agent | What It Does |
|---|---|
| **Log Intelligence** | Parses logs, detects brute-force patterns, builds root-cause chains, streams findings in real time |
| **Code Intelligence** | 3-pass analysis: AST structure (Pass 1) → semantic LLM review (Pass 2) → OWASP vulnerability scan (Pass 3) |
| **Security & Supply-Chain** | Detects hallucinated dependencies, typosquatted packages, and OWASP-classified vulnerabilities |
| **Performance** | Monitors CPU/RAM/disk, surfaces degradation patterns before they become incidents |
| **Self-Heal** | Previews, approves, and relays fix commands to remote agents via a double-whitelisted relay system |
| **Agentic Loop** | 6-step autonomous reasoning: Ingest → Triage → Root Cause → Fix Plan → Heal → Verify |

---

## 🖥️ Two Surfaces. Zero Context Switching.

LogOracle lives where developers work — the terminal and the editor. No browser tab required.

### 1. Terminal Agent (Python CLI · Textual TUI)

```bash
# Install
pip install textual httpx psutil python-dotenv

# Set API key
export LOGORACLE_API_KEY=your-api-key

# Run
python logoracle_cli.py --watch /var/log/auth.log
```

**TUI layout:**
- ASCII logo + live status panel
- CPU / RAM / Disk bars (live, color-coded)
- Backend health indicator
- Color-coded live log tail
- Findings panel (Sev · Time · Agent · Message)
- AI chat panel (press `t` to toggle)

**Flags:**

| Flag | Description |
|---|---|
| `--watch <path>` | Log file to monitor |
| `--perf` | Enable system performance monitoring |
| `--api` | Enable API traffic monitoring |
| `--relay` | Register as a heal relay agent |
| `--agent-id <id>` | Set agent identity |
| `--paste` | Paste log text directly |
| `--ingest <path>` | One-shot ingest a log file |

**Keybinds:** `q` quit · `c` clear log · `f` clear findings · `t` toggle chat

---

### 2. VS Code Extension (`.vsix`)

**Install:** VS Code → Extensions → `···` → Install from VSIX → select `logoracle-vscode/logoracle-0.1.0.vsix`

**Features:**
- Inline code diagnostics (underlines issues as you code)
- Auto-analyze on save (Python, JS, TS, Java, Go, C#)
- Findings sidebar (tree view)
- Agent status sidebar
- Developer growth / XP sidebar
- AI chat panel (webview)
- Live log file watcher
- Leaderboard panel
- One-click self-heal preview + approve

**Configuration:**

| Setting | Default | Description |
|---|---|---|
| `logoracle.backendUrl` | `http://localhost:8001` | Backend URL |
| `logoracle.apiKey` | `""` | API key (X-API-Key header) |
| `logoracle.mode` | `tech` | `tech` or `plain` English output |
| `logoracle.autoAnalyzeOnSave` | `true` | Auto-scan on file save |
| `logoracle.watchLogPaths` | `[]` | Log paths to monitor |

---

## 🏗️ Architecture

```
Developer
  Terminal TUI              VS Code Extension
      |                           |
      v                           v
  FastAPI Backend (port 8001)
  39+ endpoints · SSE streaming · API key + Keycloak auth

  Log Agent | Code Agent | Security Agent | Perf Agent | Self-Heal

      |
  PostgreSQL + Redis + HashiCorp Vault
      |
  Prometheus (:9090) + Grafana (:3001) + Keycloak (:8080)
```

**Log Analysis flow:**
```
Raw logs → parser → brute-force detector → root-cause chain
                 → SSE stream → TUI findings panel
```

**Code Intelligence flow:**
```
Source file → tree-sitter AST (Pass 1)
            → GROQ LLaMA 3.1-8B semantic (Pass 2)
            → OWASP vuln scan (Pass 3)
            → ranked findings JSON
```

**Self-Heal Relay flow:**
```
Backend → relay/register → agent polls relay/pending/{id}
       → command dispatched (whitelist check)
       → result posted to relay/result/{token}
```

---

## 🔒 Security Stack

| Layer | Technology |
|---|---|
| Password hashing | Argon2id |
| Data encryption | AES-256-GCM |
| Secrets management | HashiCorp Vault (KV-v2) |
| Authentication | API Key + Keycloak OAuth2/OIDC |
| Rate limiting | slowapi + Redis |
| Audit logging | Per-request audit trail |
| Honeytokens | Trap-based intrusion detection |
| Container security | 5-container Docker, zero npm vulns |
| TLS | nginx termination (Let's Encrypt via `tls_setup.sh`) |
| Backups | AES-encrypted, 7-day retention |

---

## 📊 Observability

LogOracle monitors itself.

| Tool | Purpose | Port |
|---|---|---|
| Prometheus | Metrics scraping every 15s | 9090 |
| Grafana | 8-panel live dashboard | 3001 |
| Keycloak | Auth / SSO / RBAC | 8080 |

**Metrics tracked:**
- Request count + latency (p95) by endpoint
- Analysis pipeline duration
- Findings detected by severity and category
- Active agents count
- GROQ token usage

---

## 🚀 Quick Start

**Requirements:** Python 3.10+, Docker + Docker Compose, GROQ API key (free at [groq.com](https://groq.com))

### 1. Clone and configure

```bash
git clone https://github.com/suchitchopade3110-arch/LogOracle.git
cd LogOracle/logoracle-backend
cp .env.example .env
# Set GROQ_API_KEY and API_KEY in .env

# Important: unset shell-exported GROQ_API_KEY if set
# Shell exports override .env and cause silent auth failures
unset GROQ_API_KEY
```

### 2. Start infrastructure

```bash
# Keycloak (auth)
cd infra/keycloak && docker compose up -d

# Prometheus + Grafana (monitoring)
cd ../monitoring && docker compose up -d
```

### 3. Start backend

```bash
cd ../../logoracle-backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001
```

### 4. Launch terminal agent

```bash
cd ..
source .venv/bin/activate
pip install textual httpx psutil python-dotenv
export LOGORACLE_API_KEY=your-api-key
python logoracle_cli.py --watch /var/log/auth.log
```

### 5. Install VS Code extension

```
VS Code → Extensions → ··· → Install from VSIX
Select: logoracle-vscode/logoracle-0.1.0.vsix
Set logoracle.apiKey in VS Code settings
```

---

## 🧪 Demo: Brute Force Detection

```bash
# Inject 30 brute-force log lines to trigger findings panel
for i in $(seq 1 30); do
  echo "$(date) Failed password for root from 192.168.1.$i port 22 ssh2" >> /tmp/demo.log
  sleep 0.1
done

# Watch LogOracle detect it in real time
python logoracle_cli.py --watch /tmp/demo.log
```

> Findings panel triggers after 20-line buffer threshold — inject at least 30 lines.

**Demo sequence:**
```
1. Start backend      uvicorn main:app --host 0.0.0.0 --port 8001
2. Start TUI agent    python logoracle_cli.py --watch /tmp/demo.log
3. Run attack sim     bash inject_demo_logs.sh
4. Watch              findings panel populates → chat explains → XP awarded
5. Show               code intel scan in VS Code → heal relay preview
```

---


## 🤖 Agentic AI Loop

LogOracle ships a fully autonomous 6-step agentic loop that fires on every incident. Powered by GROQ LLaMA 3.1-8B. Every decision streamed live to Terminal TUI.

```
Log Stream → INGEST → TRIAGE → ROOT CAUSE → FIX PLAN → [Human Approval Gate] → HEAL → VERIFY → GREEN
```

| Step | What happens |
|---|---|
| **INGEST** | Parses log stream, counts events, detects platform |
| **TRIAGE** | Fires all agents concurrently, classifies health RED/ORANGE/GREEN |
| **ROOT CAUSE** | LLM identifies root cause + impact + priority |
| **FIX PLAN** | LLM generates 3 concrete shell commands / config changes |
| **HEAL** | Applies auto-fixable remediation, queues rest for human review |
| **VERIFY** | LLM generates verification checks. Final health recalculated. |

Design principles: **Human-in-the-loop** · **Zero-trust** · **Transparent** · **Deterministic fallback**

```bash
# Agentic loop (JSON)
curl -X POST http://localhost:8001/agent/run/sync \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"log_text": "Failed password for root from 192.168.1.5 port 22"}'
```

---

## 🔌 Key API Endpoints (39+ total · port 8001)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/stream/agents` | Agent status SSE stream |
| `GET` | `/stream/logs` | Live log SSE stream |
| `POST` | `/ingest/logs` | Ingest raw log lines |
| `POST` | `/analyze/log` | Log analysis + root-cause chain |
| `POST` | `/analyze/code` | 3-pass code intelligence |
| `POST` | `/analyze/hallucination` | Hallucinated dependency detection |
| `POST` | `/analyze/correlate` | Cross-signal correlation |
| `POST` | `/chat/sync` | AI chat (JSON, no SSE) |
| `POST` | `/heal/preview` | Preview fix command |
| `POST` | `/heal/approve` | Approve and execute fix |
| `POST` | `/quiz/generate` | Generate quiz from incident |
| `POST` | `/quiz/answer` | Submit answer, award XP |
| `GET` | `/leaderboard` | Developer leaderboard |
| `POST` | `/agent/run` | **Agentic loop — SSE stream (6 steps live)** |
| `POST` | `/agent/run/sync` | **Agentic loop — JSON (all steps)** |
| `GET` | `/agents/status` | Agent health status |
| `GET` | `/metrics/` | Prometheus metrics |

> SSE endpoints (`/stream/*`) are exempt from API key auth — browsers cannot set custom headers on `EventSource`.

---

## 🏆 Industry Gaps Covered

| Gap | How LogOracle Solves It |
|---|---|
| Alert fatigue → root cause | Autonomous causal chain: failed logins → IP → user → compromise |
| AI supply-chain threats | Hallucinated dependency detection — industry first |
| Safe auto-remediation | Self-heal relay with double-whitelist + preview step |
| Tool sprawl | Terminal + VS Code — no browser tab needed |
| Incident → learning | Quiz/XP system turns every incident into a learning moment |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.10) |
| Terminal UI | Textual (Python) |
| VS Code Extension | TypeScript (.vsix) |
| LLM | GROQ · LLaMA 3.1-8B-instant |
| AST Parsing | tree-sitter (venv required) |
| Database | PostgreSQL |
| Cache / Rate Limit | Redis + slowapi |
| Secrets | HashiCorp Vault (KV-v2) |
| Encryption | Argon2id · AES-256-GCM |
| Reverse Proxy | nginx |
| Monitoring | Prometheus + Grafana |
| Auth | Keycloak (OAuth2/OIDC) |
| Security Reference | OWASP · MITRE ATT&CK |

---

## ⚙️ Environment Variables

```bash
# Required
GROQ_API_KEY=gsk_...
DB_USER=logoracle
DB_PASS=logoracle123
DB_NAME=logoracle
DB_HOST=localhost
DB_PORT=5432

# Optional
API_KEY=                    # empty = no auth in dev
REDIS_HOST=localhost
REDIS_PORT=6379
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=...
VAULT_REQUIRED=false        # flip true after vault_seed.sh
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=logoracle
KEYCLOAK_CLIENT_ID=logoracle-api
```

---

## 🏭 Production Checklist

- [ ] Run `vault_seed.sh` and flip `VAULT_REQUIRED=true`
- [ ] Run `tls_setup.sh` for real TLS (Let's Encrypt)
- [ ] Verify `backup-cron` service in `docker-compose.yml`
- [ ] Restrict `ALLOWED_ORIGINS` to your domain
- [ ] Rotate `API_KEY` and `VAULT_TOKEN`
- [ ] Set `logoracle.apiKey` in VS Code settings

---


## 🌐 Run Agent on Any Machine

Your friend can run the LogOracle terminal agent against your backend from any machine.

### Prerequisites
```bash
pip install textual httpx psutil python-dotenv
```

### Connect to remote backend
```bash
# Download agent
curl -O https://raw.githubusercontent.com/suchitchopade3110-arch/LogOracle/main/logoracle_cli.py

# Set backend URL and API key
export LOGORACLE_API_KEY=your-api-key
export LOGORACLE_BASE_URL=http://your-server-ip:8001

# Watch any log file on their machine
python logoracle_cli.py --watch /var/log/syslog
```

All analysis runs on your backend — friend's logs are sent to your server for AI processing.

### Expose backend publicly (ngrok)
```bash
# On your machine
ngrok http 8001
# Share the https://xxx.ngrok.io URL with friend
```

---
## 👥 Team

Built at **Summer Code Hackathon 2026** by a 5-person team.

| Name | Role |
|---|---|
| **Suchit** | Backend, Integration, Demo |
| **Thaariha** | Chatbot & RAG |
| **Subhiksha** | LLM & Quiz/XP system |
| **Shruthi** | Log Parsing, AST/OWASP, Distros |
| **TharunBL** | Frontend (Next.js 14) |

---

## 📄 License

MIT — see [LICENSE](LICENSE)
