# LogOracle Agent

Local terminal agent — tails log files and streams findings to LogOracle backend.

## Install

```bash
pip install logoracle-agent
```

Or from source:
```bash
cd logoracle-agent
pip install -e .
```

## Usage

```bash
# Basic — tail syslog
logoracle-agent --watch /var/log/syslog

# Multiple files
logoracle-agent --watch /var/log/auth.log --watch /var/log/nginx/error.log

# With system monitoring (CPU/RAM/disk)
logoracle-agent --watch /var/log/syslog --perf

# Plain English mode
logoracle-agent --watch /var/log/syslog --mode plain

# Remote backend
logoracle-agent --url https://logoracle.onrender.com --watch /var/log/syslog

# With XP tracking
logoracle-agent --watch /var/log/syslog --dev-id your_name
```

## Dashboard

Live terminal dashboard shows:
```
┌────────────────────────────────────┐
│ Metric          │ Value            │
├─────────────────┼──────────────────┤
│ Lines sent      │ 1,247            │
│ Analyses        │ 62               │
│ Findings        │ 2 CRITICAL  3 W  │
│ Last finding    │ SSH brute-force… │
│ CPU             │ 42.3%            │
│ RAM             │ 67.8%            │
│ Disk            │ 54.2%            │
└─────────────────┴──────────────────┘
```

## How it works

```
Local log file
    ↓ tail (watchdog)
Buffer (2s flush interval)
    ↓ POST /ingest/logs
LogOracle backend (SSE broadcast)
    ↓
Browser / VS Code extension receives live findings
```

Every 20 lines buffered → triggers `/analyze/log` → findings pushed via `/stream/agents` SSE to all connected clients.
