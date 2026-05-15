# 🔮 LogOracle

> **AI Antivirus for Code. AI Doctor for Applications.**

LogOracle watches your logs, reads your code, hunts down threats, and explains everything in plain English — autonomously, in real time, before your users notice anything is wrong.

No more digging through 10,000 log lines at 3am. No more "works on my machine." No more security vulnerabilities shipping to production.

**LogOracle catches it first.** 🛡️

---

## ✨ What Makes It Special

```
🔍 Paste a log  →  Root cause identified in seconds
🧬 Save a file  →  Security issues underlined instantly
🚨 SSH attack   →  Detected, explained, fix command ready
🎓 Bug found    →  Quiz generated so you never make it again
```

---

## 🤖 Meet the 5 Agents

Every analysis runs through a team of specialized AI agents working in parallel:

### 🪵 Log Agent
Reads 12 log formats across every major platform. Drops the noise, surfaces what matters.
- Linux: `syslog` `auth.log` `dmesg` `journald` `kern.log`
- Windows: `Event Log (XML + plaintext)` `IIS` `PowerShell`
- macOS: `Unified Log` `ASL` `Crash Reports (.ips)`
- Auto-detects platform, distro, and format — zero config
- PII redacted before anything touches the AI 🔒

### 🛡️ Security Agent
Finds the threats your firewall missed.
- SSH, RDP, NTLM, macOS brute-force detection
- 11 CVE signatures (Log4Shell, PrintNightmare, EternalBlue, Zerologon + more)
- Smart popup gate — only alerts when confidence ≥ 85% (no alert fatigue)
- 5-minute cooldown between duplicate alerts

### ⚡ Performance Agent
Watches your system so you don't have to.
- Real-time CPU, RAM, disk, load average via `psutil`
- OOM kill detection, disk full warnings, load spikes
- Live SSE stream — updates every 3 seconds

### 👁️ Hallucination Agent
Catches fake packages before they reach production.
- Validates every import against PyPI, npm, NuGet, Maven — **in parallel**
- Flags hallucinated, deprecated, and valid packages
- Works on Python, JavaScript, TypeScript, C#

### 🌐 API Agent
Detects when your services are quietly dying.
- Retry storm detection (same endpoint failing repeatedly)
- Error rate spikes (>30% failure rate)
- P95 latency monitoring (>2000ms threshold)

---

## 🖥️ 3 Ways to Use It

### 🌐 Web Dashboard — Zero install, instant results
Open your browser, paste a log or click a demo scenario, and watch the agents work.

```
✅ One-click demo scenarios
✅ Live agent status bar
✅ Root cause chain (visual graph)
✅ AI chat with 5 personas
✅ Plain English / Technical toggle
✅ Self-heal approve flow
✅ PDF export + session share
✅ Team leaderboard
```

### 🧩 VS Code Extension — Never leave your editor
Findings appear inline as you code. No context switching.

```
✅ Auto-analyze on every save
✅ Red/yellow squiggles with CWE IDs
✅ AI chat panel with streaming responses
✅ Live log monitoring with popup alerts
✅ Status bar health badge 🟢/🟠/🔴
✅ Keyboard shortcut: Ctrl+Shift+L
```

### 💻 Terminal Agent — For servers and DevOps
Runs anywhere Python runs. Even over SSH.

```bash
logoracle-agent --watch /var/log/syslog --perf
```

```
✅ Tails any log file in real time
✅ Streams findings to dashboard automatically
✅ Live terminal dashboard (Rich UI)
✅ System metrics sidebar
✅ Works headless, scriptable, CI/CD friendly
```

---

## 🚀 Quick Start

### 1️⃣ Backend
```bash
git clone https://github.com/your-org/logoracle
cd logoracle-backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your GROQ_API_KEY
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 2️⃣ Web Dashboard
```bash
cd logoracle-frontend
cp .env.example .env.local  # NEXT_PUBLIC_API_URL=http://localhost:8001
npm install && npm run dev
# → http://localhost:3000 ✨
```

### 3️⃣ Terminal Agent
```bash
pip install logoracle-agent
logoracle-agent --watch /var/log/syslog --perf
```

### 4️⃣ VS Code Extension
```
Extensions → ⋯ → Install from VSIX → logoracle-0.1.0.vsix
```

---

## 🎭 10 Demo Scenarios

One click. Instant results. No setup.

| # | 🎬 Scenario | 🖥️ Platform | 🤖 Agents Triggered |
|---|-------------|-------------|---------------------|
| 01 | 🔐 SSH Brute Force | Ubuntu | Security + Log |
| 02 | 💥 OOM Kill (nginx dies) | RHEL | Log + Performance |
| 03 | 💉 SQL Injection | Python | Code + Security |
| 04 | 👻 Hallucinated Package | Python | Hallucination |
| 05 | 💾 Disk Full | Alpine | Performance + Log |
| 06 | 🌪️ Retry Storm | Any | API Agent |
| 07 | 😱 Kernel Panic | Alpine | Log |
| 08 | 🔴 Redis Memory Leak | Linux | Performance + Security |
| 09 | 🕷️ XSS Vulnerability | JavaScript | Code + Security |
| 10 | 🧠 Intent Gap Detection | Python | Code + LLM |

```bash
# Run any scenario via API
curl -X POST http://localhost:8001/demo/run/01_ssh_bruteforce
```

---

## 🔌 API Reference

### 🔬 Analysis
| | Endpoint | What it does |
|---|---|---|
| `POST` | `/analyze/log` | Full log parse + security + fix commands |
| `POST` | `/analyze/code` | AST → LLM → OWASP 3-pass scan |
| `POST` | `/analyze/hallucination` | Registry validation |
| `POST` | `/analyze/correlate` | Root cause chain builder |
| `POST` | `/analyze/api` | HTTP event anomaly detection |
| `GET`  | `/analyze/performance` | System snapshot + findings |

### 📡 Live Streams (SSE)
| | Endpoint | What it does |
|---|---|---|
| `GET` | `/stream/agents` | Agent heartbeat every 2s |
| `GET` | `/stream/logs` | Real-time log lines |
| `GET` | `/stream/performance` | CPU/RAM/disk every 3s |
| `POST` | `/chat` | AI chat with token streaming |

### 🩹 Self-Heal
| | Endpoint | What it does |
|---|---|---|
| `POST` | `/heal/preview` | Dry-run fix validation |
| `POST` | `/heal/approve` | Execute whitelisted fix |
| `GET`  | `/heal/whitelist` | View safe command patterns |

### 🎓 Growth
| | Endpoint | What it does |
|---|---|---|
| `POST` | `/quiz/generate` | MCQ from real bug |
| `POST` | `/quiz/answer` | Submit + earn XP |
| `POST` | `/quiz/schedule` | SM-2 spaced repetition |
| `GET`  | `/leaderboard` | Team XP rankings |
| `GET`  | `/badges/events` | Badge unlocks |

### 📥 Ingest
| | Endpoint | What it does |
|---|---|---|
| `POST` | `/ingest/logs` | Push log lines to stream |
| `POST` | `/ingest/api_events` | Push API events |

### 🎮 Demo
| | Endpoint | What it does |
|---|---|---|
| `GET`  | `/demo/scenarios` | List all 10 scenarios |
| `POST` | `/demo/run/{id}` | One-click scenario execution |

> Full interactive docs at `http://localhost:8001/docs` 📖

---

## 🧠 AI Chat Personas

Talk to LogOracle in the voice that fits your situation:

| Persona | 🎭 Style | Best for |
|---------|----------|----------|
| 🤖 **Default** | Helpful, concise | General debugging |
| 🏛️ **Architect** | Direct, structural, no hand-holding | Design decisions |
| 🔐 **Security** | Formal, risk-focused, CVSS scores | Security review |
| ⚡ **Performance** | Data-driven, Big-O, metrics | Optimization |
| 👨‍🏫 **Mentor** | Patient, analogies, explains WHY | Learning + growth |

---

## 🏆 XP & Growth System

Every bug you find, fix, or learn from earns you XP:

```
🐛 Correct quiz answer      → +20 XP
⚡ Answer in under 15s      → +10 XP bonus
⚖️  Dispute a finding & win  → +60 XP
🩹 Self-heal approved       → +80 XP
🔥 30-day streak            → 🏅 Badge unlocked
⭐ 1,000 XP total           → 🏅 Code Legend
```

---

## 🏗️ Architecture

```
                    ╔═════════════════════════════╗
                    ║     LogOracle Backend       ║
                    ║       FastAPI :8001         ║
                    ║                             ║
                    ║  🪵 Log      🛡️ Security    ║
                    ║  ⚡ Perf     👁️ Hallucin.   ║
                    ║  🌐 API Agent               ║
                    ║          ↕ Groq LLM         ║
                    ║      (LLaMA 3.1-8B)         ║
                    ╚══════════════┬══════════════╝
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
   ╔══════▼══════╗        ╔════════▼════════╗     ╔════════▼════════╗
   ║  🌐 Web UI  ║        ║ 🧩 VS Code Ext ║     ║ 💻 Terminal     ║
   ║  Next.js 14 ║        ║  TypeScript     ║     ║ Agent CLI       ║
   ║  :3000      ║        ║  .vsix          ║     ║ pip install     ║
   ╚═════════════╝        ╚═════════════════╝     ╚═════════════════╝
```

---

## 🛠️ Tech Stack

**Backend**
- 🐍 Python + FastAPI — async, SSE streaming
- 🤖 Groq API (LLaMA 3.1-8B) — LLM inference
- 🌳 tree-sitter — AST parsing
- 🔢 sentence-transformers — semantic embeddings
- 📊 psutil — system metrics
- 🗄️ Redis — session persistence
- 📄 WeasyPrint — PDF generation
- 🚦 slowapi — rate limiting

**Frontend**
- ⚛️ Next.js 14 + React
- 🐻 Zustand — state management
- 🌊 ReactFlow — root cause visualization
- 📝 Monaco Editor — code input
- 🎞️ Framer Motion — animations
- 📈 Recharts — metrics charts
- 🎨 Tailwind CSS — styling

**Supported Platforms**
🐧 Linux (Ubuntu · Arch · RHEL · Alpine) &nbsp; 🪟 Windows &nbsp; 🍎 macOS

**Supported Languages**
🐍 Python &nbsp; 🟨 JavaScript &nbsp; 🔷 TypeScript &nbsp; ☕ Java &nbsp; 🔵 C#

---

## 🔒 Security & Privacy

- 🔐 PII automatically redacted before AI processing (IPs, emails, usernames, paths)
- 🛡️ Self-heal whitelist — only pre-approved commands can execute
- 🔑 API key authentication (configurable)
- 🚦 Rate limiting on all endpoints
- 🌍 CORS restricted to configured origins in production
- 🗑️ No log data persisted — stateless by design
- ✅ Confidence gate — alerts only when ≥ 85% confident

---

## ⚙️ Environment Variables

```bash
# Required
GROQ_API_KEY=gsk_...         # Get from console.groq.com

# Optional
API_KEY=                      # Backend API key (empty = dev mode, no auth)
ALLOWED_ORIGINS=*             # CORS origins (* for dev, URL for prod)
REDIS_HOST=localhost          # Redis for session persistence
REDIS_PORT=6379
```

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

<div align="center">

**Built with 🔥 by Team LogOracle**

*"The best debugging tool is the one that fixes the bug before you know it exists."*

[🌐 Live Demo](http://localhost:3000) &nbsp;·&nbsp; [📖 API Docs](http://localhost:8001/docs) &nbsp;·&nbsp; [🐛 Issues](https://github.com/your-org/logoracle/issues)

</div>
