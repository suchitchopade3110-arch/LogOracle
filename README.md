<div align="center">

# LogOracle 🛡️

**AI Antivirus for Code. AI Doctor for Applications. AI Guardian for Developers.**

*Autonomous AI debugging platform — watches your stack, finds root causes, teaches your team.*

[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![GROQ](https://img.shields.io/badge/AI-GROQ%20%2B%20LLaMA%203.1-orange)](https://groq.com)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

</div>

---

## What Is LogOracle?

Most debugging tools wait for you to act. LogOracle doesn't.

The moment your session starts, five AI agents activate silently in the background — monitoring logs, APIs, security events, performance, and AI-generated code. When something breaks, LogOracle already knows why, shows you the full causal chain, and suggests the exact fix.

```
Session starts
    ↓
5 AI agents activate (zero user action required)
    ↓
Correlation Engine builds Root Cause Chain
    ↓
Severity classified → CRITICAL / WARNING / INFO
    ↓
Health Badge updates · Smart Popup fires · Self-Heal suggested
```

---

## Three Pillars

| | Pillar | What It Does |
|-|--------|--------------|
| 🦠 | **Autonomous Monitoring** | 5 agents watch logs, APIs, security, performance, and AI-generated code |
| 🔬 | **Code Intelligence** | AST + LLM + OWASP 3-pass bug detection, auto-fix, hallucination scanning |
| 🎮 | **Developer Growth** | Real bugs → quiz questions → XP → badges → team leaderboard |

---

## Features

### 🤖 Autonomous Multi-Agent Monitoring

Five specialized agents run in parallel from the moment the app loads:

| Agent | What It Watches |
|-------|----------------|
| **Log Agent** | syslog, dmesg, journald, auth.log, kern.log, app logs |
| **API Agent** | HTTP/HTTPS requests, response codes, latency, retry storms |
| **Security Agent** | Brute-force patterns, auth failures, CVE signatures |
| **Performance Agent** | CPU, RAM, disk I/O, OOM events |
| **Hallucination Agent** | AI-generated imports, API method existence, library versions |

All agent findings flow into the **Correlation Engine**, which builds a causal chain across layers automatically — no human input required.

**Example Root Cause Chain:**
```
[Security Agent]    SSH brute-force: 847 attempts @ 02:14:03  →  CRITICAL
[Log Agent]         sshd spawning excessive child processes   @ 02:14:11
[Performance Agent] RAM spike: 78% → 94%                     @ 02:14:18
[Log Agent]         OOM killer terminated nginx               @ 02:14:23
[API Agent]         POST /api/* returning 503                 @ 02:14:24
[Log Agent]         kern.log: kernel panic - not syncing      @ 02:14:31

ROOT CAUSE: SSH brute-force attack  |  CONFIDENCE: 94%
FIX: sudo ufw deny from <attacker-ip> && sudo systemctl restart nginx
```

**Notification design — intelligent, never noisy:**
- **Health Badge** — always visible, never blocks UI. Green / Orange / Red.
- **Severity Counter** — live count of Critical · Warning · Info findings.
- **Smart Popup** — fires only for CRITICAL findings with high confidence. Max once per 5 minutes.
- **Silent findings** — everything else logged quietly, viewable on demand.

---

### 🔍 Code Intelligence Engine

Every code submission runs three sequential analysis passes:

| Pass | Layer | Technique | Catches |
|------|-------|-----------|---------|
| 1 | Syntactic | AST parsing (tree-sitter) | Unreachable code, type mismatches, syntax errors |
| 2 | Semantic | LLM inference (GROQ + LLaMA 3.1) | Logic bugs, null dereference, race conditions |
| 3 | Security | OWASP rule engine + LLM | SQL injection, XSS, hardcoded secrets |

**Additional capabilities:**

- **Auto-Fix Engine** — generates confidence-scored patches. Fixes below 70% confidence shown as suggestions only, never auto-applied.
- **Intent vs. Implementation Gap** — detects when your code diff diverges from what your PR description says it does.
- **Cross-PR Conflict Detection** — finds same-function edits across concurrent open submissions.
- **Code Health Score** — 0–100 per file, weighted across complexity, test coverage, defect density, duplication, and open issues.
- **Business Impact Scoring** — files tagged PAYMENTS/AUTH require 2 human reviewers before merge; DOCS/CONFIG can auto-merge.
- **Hallucination Detection** — validates every import and API call against live PyPI, npm, and Maven registries. Catches fake functions before they hit runtime.

**Supported languages:** Python · JavaScript · TypeScript · Java · Go · Generic

---

### 💬 AI Chatbot

Conversational interface with full session context — all findings, logs, diffs, and chat history injected on every message.

Switch analysis focus with persona slash commands:

| Command | Persona | Style |
|---------|---------|-------|
| `/persona architect` | Senior Architect | Design patterns, coupling, scalability |
| `/persona security` | Security Auditor | OWASP Top 10, threat modelling, data flow |
| `/persona perf` | Performance Freak | Complexity, hot paths, I/O patterns |
| `/persona mentor` | Mentor | Analogies, gentle corrections, educational |

**Dispute flow** — disagree with a finding? Push back in chat. The AI re-evaluates with additional context and may downgrade or retract.

**Predictive warnings** — before you close a session, the chatbot checks whether the current error pattern matches past incidents in the same codebase and warns proactively.

---

### 🎮 Developer Growth System

Every bug LogOracle finds becomes a personalized quiz question — generated from the actual error, validated, and scheduled via spaced repetition (SM-2 algorithm).

**Earn XP for:**

| Action | XP |
|--------|----|
| Quiz correct answer | +50 XP |
| Quiz correct within 15 seconds | +70 XP |
| Self-heal approved | +80 XP |
| AI finding successfully disputed | +60 XP |
| Root cause chain manually identified first | +100 XP |
| 7-day streak maintained | +150 XP |

**Badges:**

| Badge | Unlock Condition |
|-------|-----------------|
| 🛡️ Bug Slayer | 10 bugs resolved |
| ⚡ Speed Fixer | Self-heal approved within 5 seconds |
| 🏆 Quiz Master | 10 consecutive correct answers |
| 🔒 Security Expert | Pass 20-question security quiz ≥ 85% |
| 🔥 30-Day Streak | 1 quiz/day for 30 consecutive days |
| ⭐ Code Legend | 1,000 XP total |
| ⚖️ Dispute Champion | 5 AI findings successfully disputed |
| ⛓️ Chain Breaker | Resolve a root cause chain spanning 4+ agents |

**Team Leaderboard** — Rank · XP this week · XP all time · Streak · Top Badge. Refreshes every 60 seconds. Privacy opt-out available.

---

## How to Use

### Input Methods

| Method | How |
|--------|-----|
| Paste log text | Drop raw log content into the Log Analysis textarea |
| Upload log file | Drag and drop `.log` / `.txt` / `.gz` — multi-file supported |
| Multi-file correlation | Drop 3+ files — Correlation Engine runs cross-file root cause |
| Paste code | Monaco editor auto-detects language; triggers full 3-pass analysis |
| Live stream | SSE tail from journald/syslog — analysis updates as lines arrive |

### Plain English Mode

One toggle converts every technical finding into jargon-free language. A non-technical user and a senior engineer can use the same platform without changing anything else.

---

## Tech Stack

```
Frontend    Next.js 14 · Tailwind CSS · shadcn/ui · Zustand · ReactFlow · Monaco Editor · Recharts · Framer Motion
Backend     FastAPI (Python)
AI          GROQ API — LLaMA 3.1-8B
AST         tree-sitter
Embeddings  sentence-transformers
Streaming   Server-Sent Events (SSE)
PDF Export  WeasyPrint
```

---

## Getting Started

### Prerequisites

```
Node.js >= 18
Python >= 3.11
GROQ API key — free at console.groq.com
```

### 1. Clone

```bash
git clone https://github.com/your-org/logoracle.git
cd logoracle
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Add GROQ_API_KEY to .env
uvicorn main:app --reload
```

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL to your backend URL
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Agents activate immediately.

---

## Architecture

```
Browser (Next.js)
  ├── SSE client ──────────────────→ /stream/logs    (real-time log tail)
  ├── SSE client ──────────────────→ /stream/agents  (agent status + findings)
  ├── Zustand store ────────────────  all session state, no prop drilling
  └── ReactFlow ────────────────────  Root Cause Chain visualization

Backend (FastAPI)
  ├── GROQ API (LLaMA 3.1-8B) ─────  all LLM calls
  ├── tree-sitter ──────────────────  AST parsing + fix validation
  ├── sentence-transformers ────────  intent-gap + predictive flagging
  ├── PyPI / npm / Maven APIs ──────  hallucination registry check
  ├── SM-2 scheduler ──────────────  quiz delivery timing
  └── WeasyPrint ───────────────────  PDF export
```

**Stateless by design** — no database. All state lives in the session. Nothing persisted server-side.

---

## Privacy

- Logs and code are **never stored** server-side
- PII (IPs, usernames, emails) auto-redacted before AI processing
- Sensitive log types (auth.log) trigger an on-screen notice
- Self-heal commands always show a dry-run preview — destructive actions require double confirmation
- Leaderboard participation is opt-out per user

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stream/logs` | GET | SSE — real-time log tail + analysis |
| `/stream/agents` | GET | SSE — agent status, health score, findings |
| `/analyze/log` | POST | On-demand log analysis |
| `/analyze/correlate` | POST | Multi-file cross-log correlation |
| `/analyze/code` | POST | 3-pass bug detection pipeline |
| `/analyze/hallucination` | POST | AI-generated code import validation |
| `/analyze/intent` | POST | Intent vs. implementation gap check |
| `/heal/approve` | POST | Execute approved self-heal command |
| `/quiz/generate` | POST | Generate MCQ from bug record |
| `/quiz/answer` | POST | Submit answer + award XP |
| `/leaderboard` | GET | Team leaderboard |
| `/export/pdf` | POST | Generate PDF session report |
| `/health` | GET | Backend health check |

---

## Contributing

```bash
# Fork → branch → PR
git checkout -b feature/your-feature
git commit -m "feat: describe your change"
git push origin feature/your-feature
# Open PR against main
```

Please open an issue first for major changes. All contributions welcome.

---

## License

MIT — see [LICENSE](LICENSE)

---

<div align="center">

*"Every other tool waited for you to act. LogOracle acted for you. And then it made sure you learned from it."*

</div>
