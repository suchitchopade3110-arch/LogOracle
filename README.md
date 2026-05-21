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
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## 🧠 What Makes LogOracle Different

| Capability | LogOracle | Traditional Tools |
|---|---|---|
| Autonomous log monitoring | ✅ Zero config | ❌ Manual setup |
| Root-cause causal chaining | ✅ Full chain | ❌ Single alert |
| Supply-chain / hallucination detection | ✅ Built-in | ❌ Not supported |
| 3-pass code intelligence (AST + LLM + OWASP) | ✅ All three | ❌ Partial |
| Self-heal relay (remote command execution) | ✅ Whitelisted | ❌ Not supported |
| Developer growth + quiz/XP system | ✅ Built-in | ❌ Not supported |
| Works in VS Code and terminal | ✅ Both surfaces | ❌ One surface |

---

## 🤖 The Five Agents

The moment LogOracle starts, five agents activate in the background — no user action required.

| Agent | What It Does |
|---|---|
| **Log Intelligence** | Parses logs, detects brute-force patterns, builds root-cause chains, streams findings in real time |
| **Code Intelligence** | 3-pass analysis: AST structure (Pass 1) → semantic LLM review (Pass 2) → OWASP vulnerability scan (Pass 3) |
| **Security & Supply-Chain** | Detects hallucinated dependencies, typosquatted packages, and OWASP-classified vulnerabilities |
| **Performance** | Monitors CPU/RAM/disk, surfaces degradation patterns before they become incidents |
| **Self-Heal** | Previews, approves, and relays fix commands to remote agents via a double-whitelisted relay system |

---

## 🖥️ Three Surfaces



### 2. VS Code Extension (`.vsix`)
Code intelligence and chatbot inline inside your editor. No context switching.

### 3. Terminal Agent (Python CLI · Textual TUI)

```bash
# Install
pip install -r requirements.txt

# Run
python logoracle_cli.py --watch /var/log/auth.log --perf --api --agent-id demo-01
```

**TUI layout:** ASCII logo + live stats panel (CPU/RAM/Disk bars, agent status) · color-coded log tail · findings panel

**Flags:**

| Flag | Description |
|---|---|
| `--watch <path>` | Log file(s) to monitor |
| `--perf` | Enable system performance monitoring |
| `--api` | Enable API traffic monitoring |
| `--relay` | Register as a heal relay agent |
| `--agent-id <id>` | Set agent identity (default: hostname + timestamp) |

**Keybinds:** `q` quit · `c` clear log · `f` clear findings

---

## ⚡ Quick Start

### Prerequisites

- Python 3.11+ with virtualenv (required — tree-sitter needs venv)
- Node.js 18+
- Docker + Docker Compose
- Redis
- PostgreSQL

### 1. Backend

```bash
# Clone and enter project
git clone https://github.com/your-org/logoracle.git
cd logoracle

# Create and activate virtualenv (required for tree-sitter)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set GROQ_API_KEY and DB credentials

# ⚠️ Important: unset shell-exported GROQ_API_KEY if set
# Shell exports override .env — this will cause silent auth failures
unset GROQ_API_KEY

# Start backend
uvicorn main:app --host 0.0.0.0 --port 8001
```

### 2. Frontend

```bash
cd logoracle-frontend
npm install
npm run dev
# → http://localhost:3000
```

### 3. Full Stack (Docker)

```bash
docker compose up -d
```

Five containers: `nginx` · `fastapi` · `postgres` · `redis` · `vault`

---

## 🔌 API Endpoints (54 total · port 8001)

### Core

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/` | Root |

### Streaming (SSE)

> ⚠️ SSE endpoints are exempt from API key auth — browsers cannot set custom headers on `EventSource`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/stream/agents` | Agent status stream |
| `GET` | `/stream/logs` | Live log stream |
| `GET` | `/stream/performance` | Live performance metrics |

### Ingest

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ingest/logs` | Ingest raw log lines |
| `POST` | `/ingest/api_events` | Ingest API traffic events |

### Analysis

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/analyze/log` | Log analysis (brute-force, root-cause chain) |
| `POST` | `/analyze/code` | 3-pass code intelligence |
| `POST` | `/analyze/semantic` | Semantic LLM analysis |
| `POST` | `/analyze/hallucination` | Supply-chain / hallucinated dependency detection |
| `POST` | `/analyze/correlate` | Cross-signal correlation |
| `GET/POST` | `/analyze/performance` | Performance analysis |
| `POST` | `/analyze/api` | API traffic analysis |
| `POST` | `/analyze/intent` | Intent gap detection |
| `POST` | `/analyze/fix` | Fix suggestion generation |
| `GET/POST` | `/analyze/fix/config` | Fix configuration |

### Chat

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | SSE streaming chat (use from browser) |
| `POST` | `/chat/sync` | Plain JSON chat (use from backend/agent — avoids SSE threading issue) |
| `POST` | `/assistant/chat` | Assistant chat variant |
| `DELETE` | `/session/{session_id}` | Clear chat session |

### Self-Heal

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/heal/preview` | Preview fix command before execution |
| `POST` | `/heal/approve` | Approve and execute fix |
| `POST` | `/heal/block-options` | Get blocking options |
| `GET` | `/heal/whitelist` | View allowed commands |
| `POST` | `/heal/relay/register` | Register remote agent |
| `GET` | `/heal/relay/agents` | List registered agents |
| `GET` | `/heal/relay/pending/{agent_id}` | Poll pending commands for agent |
| `POST` | `/heal/relay/result/{token}` | Submit command result |
| `GET` | `/heal/relay/status/{token}` | Check command status |

### Quiz / XP / Badges

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/quiz/generate` | Generate quiz question from incident context |
| `POST` | `/quiz/answer` | Submit answer — awards XP |
| `POST` | `/quiz/schedule` | Schedule future quiz |
| `GET` | `/quiz/due/{developer_id}` | Get due quizzes |
| `POST` | `/streak/check` | Check and update streak |
| `GET` | `/badges/events` | Badge trigger events |
| `GET` | `/badges/all` | All badges |

### Leaderboard

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/leaderboard` | Get leaderboard |
| `POST` | `/leaderboard/update` | Update score |
| `GET` | `/leaderboard/export/csv` | Export as CSV |

### Session & Export

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/session/share` | Generate shareable session link |
| `GET` | `/session/restore/{token}` | Restore shared session |
| `GET` | `/session-export` | Export current session |
| `POST` | `/session-export/generate` | Generate export |
| `POST` | `/session-export/copy-link` | Copy session link |
| `POST` | `/export/pdf` | Export findings as PDF |
| `GET` | `/export/pdf/preview` | Preview PDF export |

### Frontend Helpers

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/root-cause-chain` | Root cause chain data |
| `GET` | `/recommendation` | Recommendations |
| `GET` | `/developer-growth` | Growth metrics |
| `GET` | `/log-analysis` | Log analysis summary |
| `POST` | `/log-analysis/redact` | PII redaction |
| `GET` | `/alerts` | Current alerts |
| `POST` | `/recommendation/{rec_id}/execute` | Execute recommendation |

### Demo

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/demo/scenarios` | List demo scenarios |
| `POST` | `/demo/run/{scenario_id}` | Run demo scenario |

---

## 🏗️ Architecture

```
                    ┌─────────────────┐
                    │   GROQ Cloud    │
                    │  LLaMA 3.1-8B  │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
   ┌──────▼──────┐  ┌────────▼───────┐  ┌──────▼──────┐
   │  FastAPI    │  │  PostgreSQL    │  │   Redis     │
   │  :8001      │  │  (XP/badges)  │  │  (rate lim) │
   └──────┬──────┘  └────────────────┘  └─────────────┘
          │              Vault (secrets)
          │
   ┌──────▼──────────────────────────────────────┐
   │                  nginx                      │
   └──────┬──────────────────────────────────────┘
          │
   ┌──────┼──────────────────┐
   │      │                  │
┌──▼───┐ ┌▼──────────────┐ ┌▼──────────────┐
│ Web  │ │  VS Code Ext  │ │ Terminal TUI  │
│:3000 │ │    .vsix      │ │  Python CLI   │
└──────┘ └───────────────┘ └───────────────┘
```

### Data Flows

**Log Analysis:**
```
Raw logs → parser → brute-force detector → root-cause chain
                 → SSE stream → TUI findings panel
                   (findings trigger at 20-line buffer threshold)
```

**Code Intelligence:**
```
Source file → tree-sitter AST (Pass 1)
            → GROQ LLaMA 3.1-8B semantic (Pass 2)
            → OWASP vuln scan (Pass 3)
            → ranked findings JSON
```

**Chat:**
```
User msg → /chat/sync → RAG module → cosine similarity search
                      → GROQ LLaMA 3.1-8B → response
                      (per-user session_id, shared GROQ client)
```

**Self-Heal Relay:**
```
Backend → /heal/relay/register → agent polls /heal/relay/pending/{id}
       → command dispatched → agent executes (whitelist check)
       → result posted to /heal/relay/result/{token}
```

---

## 🔒 Security

- **Secrets:** HashiCorp Vault (KV-v2) — dev fallback to `.env`
- **Passwords:** Argon2id hashing
- **Data at rest:** AES-256-GCM encryption
- **Rate limiting:** Redis-backed (slowapi) on all endpoints
- **Auth:** API key middleware — SSE endpoints exempt (browser `EventSource` limitation)
- **PII redaction:** IPs, emails, usernames, paths auto-stripped from all log analysis
- **Heal relay:** Double-whitelist — command must pass both backend and agent whitelist
- **Honeytokens:** Trap credentials that alert on access
- **Audit logging:** All actions logged
- **TLS:** nginx termination (production: Let's Encrypt via `tls_setup.sh`)
- **Backups:** AES-encrypted, 7-day retention, `backup-cron` service

---

## 🚀 Demo

### Attack Simulation

```bash
# Inject 30 brute-force log lines to trigger findings panel
for i in $(seq 1 30); do
  echo "$(date) Failed password for root from 192.168.1.$i port 22 ssh2" >> /var/log/auth.log
  sleep 0.1
done
```

> ⚠️ Findings panel requires 20-line buffer threshold — inject at least 30 lines.

### Demo Sequence

```
1. Start backend:   uvicorn main:app --host 0.0.0.0 --port 8001
2. Start agent:     python logoracle_cli.py --perf --api --agent-id demo-01
3. Run attack sim:  bash inject_demo_logs.sh
4. Watch:           findings panel populates → chatbot explains → XP awarded
5. Show:            code intel scan, heal relay preview, quiz question
```

---

## ⚙️ Environment Variables

```bash
# Required
GROQ_API_KEY=gsk_...           # Groq API key
DATABASE_URL=postgresql://...  # PostgreSQL connection string

# Optional
API_KEY=                       # Backend API key (empty = no auth in dev)
ALLOWED_ORIGINS=*              # CORS (restrict in production)
REDIS_HOST=localhost
REDIS_PORT=6379
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=...
VAULT_REQUIRED=false           # Set true after vault_seed.sh
```

> ⚠️ If `GROQ_API_KEY` is exported in your shell, it overrides `.env`. Run `unset GROQ_API_KEY` before starting uvicorn.

---

## 🏭 Production Checklist

- [ ] Run `vault_seed.sh` → flip `VAULT_REQUIRED=true`
- [ ] Run `tls_setup.sh` → replace self-signed certs (Let's Encrypt)
- [ ] Verify `backup-cron` service running in `docker-compose.yml`
- [ ] Restrict `ALLOWED_ORIGINS` to your domain
- [ ] Rotate `API_KEY` and `VAULT_TOKEN`

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11) |
| Frontend | Next.js 14 (TypeScript) |
| Terminal UI | Textual (Python) |
| VS Code Extension | TypeScript (.vsix) |
| LLM | GROQ · LLaMA 3.1-8B-instant |
| AST Parsing | tree-sitter (virtualenv required) |
| Database | PostgreSQL |
| Cache / Rate Limit | Redis + slowapi |
| Secrets | HashiCorp Vault (KV-v2) |
| Encryption | Argon2id · AES-256-GCM |
| Reverse Proxy | nginx |
| Container | Docker Compose (5 containers) |
| Security Reference | OWASP · MITRE ATT&CK |

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

## 🔗 Built With

[Groq](https://groq.com) · [FastAPI](https://fastapi.tiangolo.com) · [Next.js](https://nextjs.org) · [tree-sitter](https://tree-sitter.github.io) · [Textual](https://textual.textualize.io) · [HashiCorp Vault](https://vaultproject.io)
