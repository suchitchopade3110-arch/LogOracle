"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const findings_provider_1 = require("./providers/findings_provider");
const agents_provider_1 = require("./providers/agents_provider");
const growth_provider_1 = require("./providers/growth_provider");
const chat_panel_1 = require("./panels/chat_panel");
const diagnostics_1 = require("./diagnostics");
const client_1 = require("./client");
const log_watcher_1 = require("./log_watcher");
const status_bar_1 = require("./status_bar");
let logWatcher;
let diagnostics;
let statusBar;
async function activate(ctx) {
    const config = vscode.workspace.getConfiguration("logoracle");
    const client = new client_1.LogOracleClient(config.get("backendUrl", "http://localhost:8001"));
    // Status bar — health badge
    statusBar = new status_bar_1.StatusBarManager(ctx, client);
    statusBar.start();
    // Diagnostics — inline code issue underlines
    diagnostics = new diagnostics_1.DiagnosticsManager(ctx);
    // Tree view providers
    const findingsProvider = new findings_provider_1.FindingsProvider(ctx);
    const agentsProvider = new agents_provider_1.AgentsProvider(ctx, client);
    const growthProvider = new growth_provider_1.GrowthProvider(ctx);
    vscode.window.registerTreeDataProvider("logoracle.findings", findingsProvider);
    vscode.window.registerTreeDataProvider("logoracle.agents", agentsProvider);
    vscode.window.registerTreeDataProvider("logoracle.growth", growthProvider);
    // ── Commands ────────────────────────────────────────────────────────────
    ctx.subscriptions.push(
    // Analyze current file (code)
    vscode.commands.registerCommand("logoracle.analyzeFile", async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor)
            return;
        const code = editor.document.getText();
        const language = editor.document.languageId;
        const mode = config.get("mode", "tech");
        vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: "LogOracle: Analyzing..." }, async () => {
            try {
                const result = await client.analyzeCode(code, language, mode);
                findingsProvider.updateCodeIssues(result.issues || []);
                diagnostics.applyIssues(editor.document, result.issues || []);
                statusBar.updateFromCodeResult(result);
                const count = result.issues?.length || 0;
                vscode.window.showInformationMessage(count > 0
                    ? `LogOracle: ${count} issue(s) found — see Findings panel`
                    : "LogOracle: No issues found ✓");
            }
            catch (e) {
                vscode.window.showErrorMessage(`LogOracle: ${e.message}`);
            }
        });
    }), 
    // Analyze log file
    vscode.commands.registerCommand("logoracle.analyzeLog", async (uri) => {
        const fileUri = uri || vscode.window.activeTextEditor?.document.uri;
        if (!fileUri) {
            vscode.window.showErrorMessage("LogOracle: No file selected.");
            return;
        }
        const bytes = await vscode.workspace.fs.readFile(fileUri);
        const logText = Buffer.from(bytes).toString("utf-8");
        const mode = config.get("mode", "tech");
        vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: "LogOracle: Analyzing log..." }, async () => {
            try {
                const result = await client.analyzeLog(logText, true, mode);
                findingsProvider.updateLogFindings(result.security_findings || []);
                statusBar.updateFromLogResult(result);
                if (result.pii_detected) {
                    vscode.window.showWarningMessage(result.pii_banner || "PII detected and redacted.");
                }
                const count = result.security_findings?.length || 0;
                vscode.window.showInformationMessage(`LogOracle: ${result.platform}/${result.distro} — ${count} finding(s)`);
            }
            catch (e) {
                vscode.window.showErrorMessage(`LogOracle: ${e.message}`);
            }
        });
    }), 
    // Open AI Chat panel
    vscode.commands.registerCommand("logoracle.openChat", () => {
        chat_panel_1.ChatPanel.createOrShow(ctx.extensionUri, client);
    }), 
    // Toggle plain/tech mode
    vscode.commands.registerCommand("logoracle.toggleMode", async () => {
        const current = config.get("mode", "tech");
        const next = current === "tech" ? "plain" : "tech";
        await config.update("mode", next, vscode.ConfigurationTarget.Global);
        statusBar.updateMode(next);
        vscode.window.showInformationMessage(`LogOracle: Mode → ${next === "plain" ? "🌐 Plain English" : "⚙️ Technical"}`);
    }), 
    // Start live log monitoring
    vscode.commands.registerCommand("logoracle.watchLogs", async () => {
        const paths = config.get("watchLogPaths", []);
        if (paths.length === 0) {
            const picked = await vscode.window.showInputBox({
                prompt: "Enter log file path to monitor",
                placeHolder: "/var/log/syslog",
            });
            if (!picked)
                return;
            paths.push(picked);
            await config.update("watchLogPaths", paths, vscode.ConfigurationTarget.Global);
        }
        logWatcher = new log_watcher_1.LogWatcher(paths, client, findingsProvider, statusBar);
        logWatcher.start();
        vscode.window.showInformationMessage(`LogOracle: Monitoring ${paths.length} log file(s)...`);
    }), 
    // Stop monitoring
    vscode.commands.registerCommand("logoracle.stopWatch", () => {
        logWatcher?.stop();
        logWatcher = undefined;
        vscode.window.showInformationMessage("LogOracle: Log monitoring stopped.");
    }), 
    // Show leaderboard
    vscode.commands.registerCommand("logoracle.showLeaderboard", async () => {
        try {
            const data = await client.getLeaderboard();
            const panel = vscode.window.createWebviewPanel("logoracle.leaderboard", "LogOracle Leaderboard", vscode.ViewColumn.Beside, { enableScripts: false });
            panel.webview.html = _leaderboardHtml(data.leaderboard || []);
        }
        catch (e) {
            vscode.window.showErrorMessage(`LogOracle: ${e.message}`);
        }
    }));
    // Auto-analyze on save
    ctx.subscriptions.push(vscode.workspace.onDidSaveTextDocument(async (doc) => {
        if (!config.get("autoAnalyzeOnSave", true))
            return;
        const lang = doc.languageId;
        if (!["python", "javascript", "typescript", "java", "csharp", "go"].includes(lang))
            return;
        const mode = config.get("mode", "tech");
        try {
            const result = await client.analyzeCode(doc.getText(), lang, mode);
            diagnostics.applyIssues(doc, result.issues || []);
            findingsProvider.updateCodeIssues(result.issues || []);
            statusBar.updateFromCodeResult(result);
        }
        catch { }
    }));
    // Start agent SSE stream
    agentsProvider.startStream();
    vscode.window.showInformationMessage("LogOracle activated ✓");
}
function deactivate() {
    logWatcher?.stop();
    statusBar?.stop();
}
function _leaderboardHtml(entries) {
    const rows = entries.slice(0, 10).map((e, i) => `
        <tr>
            <td>${i + 1}</td>
            <td>${e.name}</td>
            <td>${e.xp_total}</td>
            <td>${e.xp_this_week}</td>
            <td>${e.streak_days}d</td>
            <td>${e.badges?.slice(0, 2).join(", ") || "—"}</td>
        </tr>`).join("");
    return `<!DOCTYPE html><html><head><style>
        body { font-family: var(--vscode-font-family); color: var(--vscode-foreground); padding: 16px; }
        h2 { color: var(--vscode-textLink-foreground); }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--vscode-widget-border); }
        th { color: var(--vscode-textLink-foreground); font-size: 11px; text-transform: uppercase; }
    </style></head><body>
        <h2>LogOracle Leaderboard</h2>
        <table><tr><th>#</th><th>Name</th><th>XP Total</th><th>This Week</th><th>Streak</th><th>Badges</th></tr>
        ${rows}
        </table>
    </body></html>`;
}
//# sourceMappingURL=extension.js.map