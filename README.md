# LogOracle

**AI Antivirus for Code. AI Doctor for Applications.**

LogOracle is an autonomous debugging and security intelligence platform. It monitors your logs, analyzes your code, detects threats in real time, and explains everything in plain English — inside your browser, your editor, or your terminal.

---

## What It Does

| Capability | Description |
|---|---|
| **Autonomous Log Monitoring** | Parses syslog, auth.log, dmesg, journald, Windows Event Log, macOS unified logs. Detects brute-force attacks, OOM kills, kernel panics, CVEs — automatically. |
| **3-Pass Code Intelligence** | AST syntax check → LLM semantic analysis → OWASP A01-A08 security scan. Catches SQL injection, hardcoded secrets, command injection, insecure deserialization, and more. |
| **Hallucination Detection** | Validates every import against PyPI, npm, NuGet, and Maven in parallel. Catches fake/hallucinated packages before they reach production. |
| **Self-Heal Engine** | Generates distro-aware fix commands (Ubuntu, Arch, RHEL, Alpine, Windows, macOS). Dry-run preview before approval. Whitelisted execution only. |
| **Developer Growth** | Context-aware MCQ quizzes generated from real bugs found in your code. SM-2 spaced repetition, XP system, streak tracking, badge unlocks, team leaderboard. |

---

## 5 Agents

```
┌─────────────────────────────────────────────────────────────┐
│                     LogOracle Agents                        │
├──────────────────┬──────────────────────────────────────────┤
│ Log Agent        │ Parses 12 log formats across Linux,      │
│                  │ Windows, macOS. PII redaction built in.  │
├──────────────────┼──────────────────────────────────────────┤
│ Security Agent   │ SSH/RDP/NTLM brute-force detection.      │
│                  │ CVE pattern matching. Smart popup gate.  │
├──────────────────┼──────────────────────────────────────────┤
│ Performance Agent│ Real-time CPU/RAM/disk via psutil.       │
│                  │ OOM detection, load spike alerts.        │
├──────────────────┼──────────────────────────────────────────┤
│ Hallucination    │ Live PyPI/npm/NuGet/Maven registry check.│
│ Agent            │ Flags fake packages before install.      │
├──────────────────┼──────────────────────────────────────────┤
│ API Agent        │ Retry storm detection, error rate spikes,│
│                  │ P95 latency monitoring.                  │
└──────────────────┴──────────────────────────────────────────┘
```

---

## 3 Surfaces

### 🌐 Web Dashboard
Full-featured browser UI. Zero install required.
- One-click demo scenarios
- Live agent status bar
- Root cause chain visualization (ReactFlow)
- AI chat with 5 personas (Architect, Security, Performance, Mentor, Default)
- Plain English / Technical mode toggle
- PDF export + session share

### 🧩 VS Code Extension
Analyze code without leaving your editor.
- Auto-analyze on save (Python, JS, TS, Java, C#)
- Inline red/yellow squiggles on problematic lines with CWE IDs
- Live log file monitoring with VS Code popup alerts
- AI chat panel with SSE streaming
- Status bar health badge (🟢/🟠/🔴)

### 💻 Terminal Agent
For servers, CI/CD, and DevOps workflows.
- Tail any log file in real time
- Streams findings to LogOracle backend
- Live terminal dashboard (Rich UI)
- System metrics monitoring (CPU/RAM/disk)
- Works over SSH on remote servers

---

## Quick Start

### Backend
```bash
git clone https://github.com/your-org/logoracle
cd logoracle-backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # add your GROQ_API_KEY
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Web Dashboard
```bash
cd logoracle-frontend
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL=http://localhost:8001
npm install
npm run dev
# → http://localhost:3000
```

### Terminal Agent
```bash
pip install logoracle-agent
logoracle-agent --watch /var/log/syslog --perf
```

### VS Code Extension
```
Extensions → ⋯ → Install from VSIX → logoracle-0.1.0.vsix
```

---

## API Endpoints

### Core Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analyze/log` | Full log parse + security findings + fix commands |
| `POST` | `/analyze/code` | AST + LLM semantic + OWASP scan |
| `POST` | `/analyze/hallucination` | Registry validation (PyPI/npm/NuGet/Maven) |
| `POST` | `/analyze/correlate` | Cross-agent root cause chain |
| `POST` | `/analyze/api` | HTTP event analysis (retry storms, latency) |
| `POST` | `/analyze/performance` | System metrics analysis |
| `GET`  | `/analyze/fix/config` | Auto-fix confidence gate settings |

### Streaming (SSE)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/stream/agents` | Live agent status every 2s |
| `GET` | `/stream/logs` | Real-time log line stream |
| `GET` | `/stream/performance` | CPU/RAM/disk metrics every 3s |
| `POST` | `/chat` | AI chat with SSE token streaming |

### Self-Heal
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/heal/preview` | Dry-run fix command validation |
| `POST` | `/heal/approve` | Execute approved fix (whitelisted only) |
| `GET`  | `/heal/whitelist` | View approved command patterns |

### Growth
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/quiz/generate` | MCQ from real bug finding |
| `POST` | `/quiz/answer` | Submit answer + XP |
| `POST` | `/quiz/schedule` | SM-2 spaced repetition update |
| `GET`  | `/quiz/due/{id}` | Questions due for review |
| `POST` | `/streak/check` | Daily streak update |
| `GET`  | `/badges/events` | Badge unlock events |
| `GET`  | `/leaderboard` | Team XP rankings |
| `POST` | `/leaderboard/update` | Update XP + action |

### Ingest
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ingest/logs` | Push log lines to stream |
| `POST` | `/ingest/api_events` | Push API events for analysis |

### Demo
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/demo/scenarios` | List all 10 demo scenarios |
| `POST` | `/demo/run/{id}` | Execute demo scenario |

### Export & Session
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/export/pdf` | Generate PDF debug report |
| `GET`  | `/export/pdf/preview` | Preview PDF template |
| `POST` | `/session/share` | Generate shareable session token |
| `GET`  | `/session/restore/{token}` | Restore session from token |
| `GET`  | `/health` | Health check |

---

## Demo Scenarios

10 pre-built scenarios covering the most common production incidents:

| # | Scenario | Platform | Agents |
|---|----------|----------|--------|
| 01 | SSH Brute Force | Ubuntu | Security, Log |
| 02 | OOM Kill | RHEL | Log, Performance |
| 03 | SQL Injection | Python | Code, Security |
| 04 | Hallucinated API Package | Python | Hallucination |
| 05 | Disk Full | Alpine | Performance, Log |
| 06 | Retry Storm | Any | API Agent |
| 07 | Kernel Panic | Alpine | Log |
| 08 | Redis Memory Leak | Linux | Performance, Security |
| 09 | XSS Vulnerability | JavaScript | Code, Security |
| 10 | Intent Gap | Python | Code, LLM |

```bash
# Run any scenario via API
curl -X POST http://localhost:8001/demo/run/01_ssh_bruteforce
```

---

## Tech Stack

### Backend
- **FastAPI** (Python) — async REST + SSE
- **Groq API** (LLaMA 3.1-8B) — LLM inference
- **tree-sitter** — AST parsing
- **sentence-transformers** — semantic embeddings
- **psutil** — system metrics
- **Redis** — session persistence (falls back to memory)
- **WeasyPrint** — PDF export
- **slowapi** — rate limiting

### Frontend
- **Next.js 14** — React framework
- **Zustand** — global state
- **ReactFlow** — root cause chain visualization
- **Monaco Editor** — code input
- **Framer Motion** — animations
- **Recharts** — metrics charts
- **Tailwind CSS** — styling

### Supported Log Formats
`syslog` `auth.log` `kern.log` `dmesg` `journald` `Windows Event Log` `IIS` `PowerShell` `macOS Unified Log` `macOS ASL` `macOS Crash Report (.ips)` `Generic`

### Supported Platforms
`Linux (Ubuntu, Arch, RHEL, Alpine)` `Windows` `macOS`

### Supported Languages (Code Analysis)
`Python` `JavaScript` `TypeScript` `Java` `C#`

---

## Architecture

```
                    ┌─────────────────────────┐
                    │     LogOracle Backend   │
                    │       FastAPI :8001     │
                    │                         │
                    │  ┌─────────────────┐   │
                    │  │   5 AI Agents   │   │
                    │  │  Log · Security │   │
                    │  │  Perf · Halluc  │   │
                    │  │  API Agent      │   │
                    │  └────────┬────────┘   │
                    │           │             │
                    │  ┌────────▼────────┐   │
                    │  │  Groq LLM API   │   │
                    │  │  LLaMA 3.1-8B   │   │
                    │  └─────────────────┘   │
                    └────────────┬────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
   ┌──────▼──────┐      ┌────────▼───────┐    ┌────────▼───────┐
   │  Web UI     │      │  VS Code Ext   │    │ Terminal Agent │
   │  Next.js    │      │  TypeScript    │    │ Python CLI     │
   │  :3000      │      │  .vsix         │    │ pip install    │
   └─────────────┘      └────────────────┘    └────────────────┘
```

---

## Environment Variables

```bash
# Required
GROQ_API_KEY=gsk_...              # Groq API key

# Optional
API_KEY=                          # Backend API key (leave empty for dev)
ALLOWED_ORIGINS=*                 # CORS origins (* for dev)
REDIS_HOST=localhost              # Redis host (falls back to memory)
REDIS_PORT=6379                   # Redis port
```

---

## Security

- PII automatically redacted from all log analysis (IPs, emails, usernames, paths)
- Self-heal commands run against a strict whitelist — no arbitrary execution
- API key authentication middleware (configurable)
- Rate limiting on all endpoints
- CORS restricted to configured origins in production
- No log data persisted — stateless by design

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Built With

- [Groq](https://groq.com) — LLM inference
- [FastAPI](https://fastapi.tiangolo.com) — backend framework
- [Next.js](https://nextjs.org) — frontend framework
- [tree-sitter](https://tree-sitter.github.io) — AST parsing
- [ReactFlow](https://reactflow.dev) — graph visualization
