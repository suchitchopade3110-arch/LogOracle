# LogOracle VS Code Extension

AI Antivirus for Code — inside your editor.

## Features

- **Auto-analyze on save** — every Python/JS/TS/Java/C# file analyzed on save
- **Inline underlines** — red/yellow/blue squiggles on problematic lines with CWE IDs
- **Live log monitoring** — tail `/var/log/syslog`, `auth.log`, any log file
- **AI Chat panel** — ask about findings with 5 personas (Architect, Security, Perf, Mentor)
- **Health badge** — status bar shows 🟢/🟠/🔴 based on current findings
- **Plain English toggle** — convert all technical findings to plain language
- **Team leaderboard** — view XP rankings inside VS Code

## Setup

1. Start LogOracle backend:
   ```bash
   cd logoracle-backend
   source venv/bin/activate
   uvicorn main:app --port 8001 --reload
   ```

2. Install extension from `.vsix` or VS Code Marketplace

3. Extension auto-connects to `http://localhost:8001`

## Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| Analyze Current File | `Ctrl+Shift+L` | Run full 3-pass analysis |
| Open AI Chat | `Ctrl+Shift+O` | Open chat panel |
| Toggle Mode | — | Switch Plain English / Technical |
| Start Log Monitoring | — | Tail local log files |
| Show Leaderboard | — | View team XP rankings |

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `logoracle.backendUrl` | `http://localhost:8001` | Backend URL |
| `logoracle.mode` | `tech` | Output mode: `tech` or `plain` |
| `logoracle.autoAnalyzeOnSave` | `true` | Analyze on every save |
| `logoracle.watchLogPaths` | `[]` | Log files to monitor |
| `logoracle.developerId` | `""` | Your ID for XP tracking |

## Build

```bash
npm install
npm run compile
npx vsce package
# → logoracle-0.1.0.vsix
```

Install `.vsix`:
```
VS Code → Extensions → ⋯ → Install from VSIX
```
