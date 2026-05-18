# 🔮 LogOracle

> **First AI debugging platform with hallucinated dependency protection.**
> **The most trustworthy AI-native debugging and security copilot for developers.**

LogOracle watches your logs, reads your code, hunts supply-chain threats, builds a causal incident graph, and explains every conclusion with evidence — autonomously, before your users notice anything is wrong.

No more digging through 10,000 log lines at 3am. No more "works on my machine." No more AI-hallucinated packages shipping to production. No more security vulnerabilities you find after the breach.

**LogOracle catches it first — and shows you exactly why.** 🛡️

---

## ✨ What Makes It Different

```
🔍 Paste a log        →  Incident Knowledge Graph built in seconds
🧬 Save a file        →  Supply-chain threats flagged before they ship
🚨 SSH attack         →  Detected, explained with evidence, fix ready
🎓 Bug resolved       →  Learning reinforcement so you never repeat it
```

> **No competitor — Datadog, Dynatrace, Sumo Logic, VoltOps — offers hallucinated package detection or typosquatting defense.**
> This is LogOracle's primary market wedge.

---

## 🛡️ Primary Differentiator — AI Supply-Chain Defense

### 👁️ Hallucination Agent — Catches Fake Packages

LLMs generating code frequently invent package names that do not exist. Developers install them. Attackers register them and embed malware. LogOracle stops this.

- Validates every import against PyPI, npm, NuGet, Maven — **in parallel**
- Flags hallucinated, typosquatted, deprecated, and unverified packages
- Works on Python, JavaScript, TypeScript, C#

### 🕵️ Typosquatting & Supply-Chain Guard — NEW

Near-miss package names are one of the fastest-growing attack vectors. LogOracle catches them before they enter your codebase.

- **Edit distance scoring** against 500k+ known packages
- **Publisher account age check** — new accounts flagged automatically
- **GitHub repository trust verification** — no repo = high risk
- **Commit delta analysis** — flags packages introduced in latest commit

**Example output:**

```
⚠  POSSIBLE SUPPLY-CHAIN ATTACK DETECTED

Package: lodahs
Reason:
  ✓ Resembles trusted package: lodash (edit distance: 2)
  ✓ Publisher account created 3 days ago
  ✗ No trusted GitHub repository found
  ✓ Dependency introduced in latest commit (2 hours ago)

Recommendation: Remove immediately. Use lodash@4.17.21 (verified).
Confidence: 97%
```

> That output is impossible without AI-era tooling. No dashboard produces this.

---

## 🧠 Incident Knowledge Graph

LogOracle converts logs, metrics, API failures, and security events into a single causal graph — allowing AI agents to trace causality across systems. Replaces 15 scattered alerts with one auditable narrative.

```
  Logs / API Events / Code / Security Signals
                     |
                     v
       Multi-Agent Analysis Layer
    (log agent + security agent + code agent)
                     |
                     v
         Incident Knowledge Graph
    (nodes = events, edges = causality)
                     |
                     v
      Confidence + Evidence Engine
  (scoring per conclusion, evidence attached)
                     |
                     v
         Fix  /  Explain  /  Learn
  (playbook | evidence panel | quiz/XP)
```

**Example causal narrative:**

```
Incident: API Saturation — Severity HIGH

Causal Chain:
  [1] Redis OOM (memory threshold exceeded at 02:14:33)
       |
  [2] Retry storm triggered (3,200 retries/min detected)
       |
  [3] API gateway saturation (p99 latency > 8s at 02:14:51)
       |
  [4] User-facing 503 outage (02:15:02)

Root cause: Redis memory configuration under-provisioned for
current traffic pattern.
```

Every node links to an evidence panel showing the exact log lines, metrics, and rules that identified it.

---

## 🔬 Confidence Scoring — Intelligence Layer, Not a UI Badge

Every AI conclusion shows a confidence percentage driven by **5 technical factors**:

| Factor | What It Measures |
|--------|-----------------|
| **Evidence count** | Independent signals (logs, metrics, traces) corroborating the conclusion |
| **Anomaly severity** | Statistical deviation from baseline, weighted by impact radius |
| **Rule match density** | OWASP, MITRE ATT&CK, and custom rules triggered |
| **Historical similarity** | Cosine similarity against known incident patterns |
| **Multi-agent agreement** | Whether log, security, and code agents independently agree |

**Example:**

```
Conclusion: Redis OOM is root cause of API outage
Confidence: 93%

Evidence:
  ✓ Redis OOM pattern matched (rule: REDIS_MEM_THRESHOLD)
  ✓ Retry storm threshold exceeded (3,200 retries/min > 500 baseline)
  ✓ API latency anomaly detected (p99 = 8.3s, baseline = 0.4s)
  ✓ Security agent consensus: no external attack vector found
  ✓ 2 prior incidents with identical causal signature (similarity: 0.91)

Agents in agreement: log-agent, security-agent, code-agent (3/3)
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
- MITRE ATT&CK mapping per finding
- Smart confidence gate — only alerts when confidence ≥ 85% (no alert fatigue)
- 5-minute cooldown between duplicate alerts

### ⚡ Performance Agent
Watches your system so you don't have to.
- Real-time CPU, RAM, disk, load average via `psutil`
- OOM kill detection, disk full warnings, load spikes
- Live SSE stream — updates every 3 seconds

### 👁️ Hallucination + Supply-Chain Agent
Catches fake and malicious packages before they reach production.
- Validates every import against PyPI, npm, NuGet, Maven — **in parallel**
- Typosquatting detection with edit distance scoring
- Publisher trust scoring — account age, repo presence, commit history
- Works on Python, JavaScript, TypeScript, C#

### 🌐 API Agent
Detects when your services are quietly dying.
- Retry storm detection (same endpoint failing repeatedly)
- Error rate spikes (>30% failure rate)
- P95 latency monitoring (>2000ms threshold)

---

## 🔒 Trust Architecture

Six layers make LogOracle's conclusions auditable and safe to act on:

| Trust Layer | How It Works |
|-------------|-------------|
| **Supply-Chain Guard** | Catches hallucinated and typosquatted packages. Evidence per finding. |
| **Confidence Scoring** | Every conclusion shows % confidence driven by 5 technical factors. No black-box output. |
| **Incident Knowledge Graph** | Full causal chain shown, not just symptoms. Full reasoning path visible. |
| **Explainability Panel** | Exact log lines, metrics, rules, and thresholds that triggered each conclusion. |
| **Multi-Agent Consensus** | Three independent agents must agree for high-confidence conclusions. Disagreement lowers score. |
| **Approval-Gated Remediation** | All automated fixes require explicit user approval. No silent changes. Safe by design. |

---

## 🖥️ 3 Ways to Use It

### 🌐 Web Dashboard — Zero install, instant results

```
✅ One-click demo scenarios
✅ Live agent status bar
✅ Incident Knowledge Graph (visual)
✅ Confidence + evidence panel per finding
✅ AI chat with 5 personas
✅ Plain English / Technical toggle
✅ Approval-gated self-heal flow
✅ PDF export + session share
✅ Team leaderboard
```

### 🧩 VS Code Extension — Never leave your editor

```
✅ Auto-analyze on every save
✅ Red/yellow squiggles with CWE IDs
✅ Supply-chain threat inline warnings
✅ AI chat panel with streaming responses
✅ Live log monitoring with popup alerts
✅ Status bar health badge 🟢/🟠/🔴
✅ Keyboard shortcut: Ctrl+Shift+L
```

### 💻 Terminal Agent — For servers and DevOps

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

> **Note:** Terminal agent is primarily tested on Linux. Windows/macOS cross-platform support is in post-MVP scope.

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
| 11 | 🕵️ Typosquatting Attack | Python | Supply-Chain Agent |

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
| `POST` | `/analyze/hallucination` | Registry validation + typosquatting check |
| `POST` | `/analyze/correlate` | Incident Knowledge Graph builder |
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
| `POST` | `/heal/approve` | Execute whitelisted fix (requires approval) |
| `GET`  | `/heal/whitelist` | View safe command patterns |

### 🎓 Growth
| | Endpoint | What it does |
|---|---|---|
| `POST` | `/quiz/generate` | MCQ from real incident root cause |
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
| `GET`  | `/demo/scenarios` | List all scenarios |
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

Persona adapts explanation depth to developer seniority — junior mode explains the why, senior mode summarises and moves fast.

---

## 🏆 Developer Learning Reinforcement

LogOracle reinforces professional skill development — not gamification. Every incident teaches as it fixes.

```
🐛 Correct quiz answer         → +20 XP
⚡ Answer in under 15s         → +10 XP bonus
⚖️  Dispute a finding & win    → +60 XP
🩹 Self-heal approved          → +80 XP
🔥 30-day streak               → 🏅 Badge unlocked
⭐ 1,000 XP total              → 🏅 Code Legend
```

- Quizzes are generated from **actual root causes** of incidents you resolved
- XP tracks growth across **security, performance, and reliability** domains
- Spaced repetition (SM-2) schedules follow-up reviews automatically

---

## ⚠️ Current Limitations

LogOracle is a hackathon MVP. Honest about what it is and is not yet.

| Limitation | Context |
|------------|---------|
| No distributed tracing | OpenTelemetry lite ingestion is in roadmap (P3) |
| Limited historical telemetry | MVP uses paste/upload inputs. Persistent storage is post-MVP. |
| Cloud log ingestion planned | CloudWatch/GCP/Azure JSON parsing not yet live |
| Deterministic engine evolving | Confidence scoring improves with broader rule coverage over time |
| Limited Windows/macOS agent depth | Terminal agent primarily tested on Linux |
| No live system agent access | MVP constraint: paste/upload, not live process hooks |

---

## 🏗️ Architecture

```
                    ╔═════════════════════════════╗
                    ║     LogOracle Backend       ║
                    ║       FastAPI :8001         ║
                    ║                             ║
                    ║  🪵 Log      🛡️ Security    ║
                    ║  ⚡ Perf     👁️ Supply-Chain ║
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
- 🔢 sentence-transformers — semantic embeddings (cosine similarity for confidence scoring)
- 📊 psutil — system metrics
- 🗄️ Redis — session persistence
- 📄 WeasyPrint — PDF generation
- 🚦 slowapi — rate limiting

**Frontend**
- ⚛️ Next.js 14 + React
- 🐻 Zustand — state management
- 🌊 ReactFlow — Incident Knowledge Graph visualization
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
- 🛡️ Self-heal whitelist — only pre-approved commands can execute, user approval required
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

*"The best debugging tool is the one that catches the threat before you write the bug."*

[🌐 Live Demo](http://localhost:3000) &nbsp;·&nbsp; [📖 API Docs](http://localhost:8001/docs) &nbsp;·&nbsp; [🐛 Issues](https://github.com/your-org/logoracle/issues)

</div>
