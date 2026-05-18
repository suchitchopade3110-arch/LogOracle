import * as vscode from "vscode";
import { FindingsProvider }   from "./providers/findings_provider";
import { AgentsProvider }     from "./providers/agents_provider";
import { GrowthProvider }     from "./providers/growth_provider";
import { ChatPanel }          from "./panels/chat_panel";
import { DiagnosticsManager } from "./diagnostics";
import { LogOracleClient }    from "./client";
import { LogWatcher }         from "./log_watcher";
import { StatusBarManager }   from "./status_bar";

let logWatcher: LogWatcher | undefined;
let diagnostics: DiagnosticsManager;
let statusBar: StatusBarManager;

export async function activate(ctx: vscode.ExtensionContext) {
    const config = vscode.workspace.getConfiguration("logoracle");
    const client = new LogOracleClient(config.get("backendUrl", "http://localhost:8001"));

    // Status bar — health badge
    statusBar = new StatusBarManager(ctx, client);
    statusBar.start();

    // Diagnostics — inline code issue underlines
    diagnostics = new DiagnosticsManager(ctx);

    // Tree view providers
    const findingsProvider = new FindingsProvider(ctx);
    const agentsProvider   = new AgentsProvider(ctx, client);
    const growthProvider   = new GrowthProvider(ctx);

    vscode.window.registerTreeDataProvider("logoracle.findings", findingsProvider);
    vscode.window.registerTreeDataProvider("logoracle.agents",   agentsProvider);
    vscode.window.registerTreeDataProvider("logoracle.growth",   growthProvider);

    // ── Commands ────────────────────────────────────────────────────────────

    ctx.subscriptions.push(
        // Analyze current file (code)
        vscode.commands.registerCommand("logoracle.analyzeFile", async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            const code     = editor.document.getText();
            const language = editor.document.languageId;
            const mode     = config.get<string>("mode", "tech");

            vscode.window.withProgress(
                { location: vscode.ProgressLocation.Notification, title: "LogOracle: Analyzing..." },
                async () => {
                    try {
                        const result = await client.analyzeCode(code, language, mode);
                        findingsProvider.updateCodeIssues(result.issues || []);
                        diagnostics.applyIssues(editor.document, result.issues || []);
                        statusBar.updateFromCodeResult(result);

                        const count = result.issues?.length || 0;
                        vscode.window.showInformationMessage(
                            count > 0
                                ? `LogOracle: ${count} issue(s) found — see Findings panel`
                                : "LogOracle: No issues found ✓"
                        );
                    } catch (e: any) {
                        vscode.window.showErrorMessage(`LogOracle: ${e.message}`);
                    }
                }
            );
        }),

        // Analyze log file
        vscode.commands.registerCommand("logoracle.analyzeLog", async (uri?: vscode.Uri) => {
            const fileUri = uri || vscode.window.activeTextEditor?.document.uri;
            if (!fileUri) {
                vscode.window.showErrorMessage("LogOracle: No file selected.");
                return;
            }

            const bytes   = await vscode.workspace.fs.readFile(fileUri);
            const logText = Buffer.from(bytes).toString("utf-8");
            const mode    = config.get<string>("mode", "tech");

            vscode.window.withProgress(
                { location: vscode.ProgressLocation.Notification, title: "LogOracle: Analyzing log..." },
                async () => {
                    try {
                        const result = await client.analyzeLog(logText, true, mode);
                        findingsProvider.updateLogFindings(result.security_findings || []);
                        statusBar.updateFromLogResult(result);

                        if (result.pii_detected) {
                            vscode.window.showWarningMessage(result.pii_banner || "PII detected and redacted.");
                        }

                        const count = result.security_findings?.length || 0;
                        vscode.window.showInformationMessage(
                            `LogOracle: ${result.platform}/${result.distro} — ${count} finding(s)`
                        );
                    } catch (e: any) {
                        vscode.window.showErrorMessage(`LogOracle: ${e.message}`);
                    }
                }
            );
        }),

        // Open AI Chat panel
        vscode.commands.registerCommand("logoracle.openChat", () => {
            ChatPanel.createOrShow(ctx.extensionUri, client);
        }),

        // Toggle plain/tech mode
        vscode.commands.registerCommand("logoracle.toggleMode", async () => {
            const current = config.get<string>("mode", "tech");
            const next    = current === "tech" ? "plain" : "tech";
            await config.update("mode", next, vscode.ConfigurationTarget.Global);
            statusBar.updateMode(next);
            vscode.window.showInformationMessage(
                `LogOracle: Mode → ${next === "plain" ? "🌐 Plain English" : "⚙️ Technical"}`
            );
        }),

        // Start live log monitoring
        vscode.commands.registerCommand("logoracle.watchLogs", async () => {
            const paths = config.get<string[]>("watchLogPaths", []);
            if (paths.length === 0) {
                const picked = await vscode.window.showInputBox({
                    prompt: "Enter log file path to monitor",
                    placeHolder: "/var/log/syslog",
                });
                if (!picked) return;
                paths.push(picked);
                await config.update("watchLogPaths", paths, vscode.ConfigurationTarget.Global);
            }

            logWatcher = new LogWatcher(paths, client, findingsProvider, statusBar);
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
                const panel = vscode.window.createWebviewPanel(
                    "logoracle.leaderboard", "LogOracle Leaderboard",
                    vscode.ViewColumn.Beside, { enableScripts: false }
                );
                panel.webview.html = _leaderboardHtml(data.leaderboard || []);
            } catch (e: any) {
                vscode.window.showErrorMessage(`LogOracle: ${e.message}`);
            }
        }),
    );

    // Auto-analyze on save
    ctx.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument(async (doc) => {
            if (!config.get<boolean>("autoAnalyzeOnSave", true)) return;
            const lang = doc.languageId;
            if (!["python","javascript","typescript","java","csharp","go"].includes(lang)) return;

            const mode = config.get<string>("mode", "tech");
            try {
                const result = await client.analyzeCode(doc.getText(), lang, mode);
                diagnostics.applyIssues(doc, result.issues || []);
                findingsProvider.updateCodeIssues(result.issues || []);
                statusBar.updateFromCodeResult(result);
            } catch {}
        })
    );

    // Start agent SSE stream
    agentsProvider.startStream();

    vscode.window.showInformationMessage("LogOracle activated ✓");
}

export function deactivate() {
    logWatcher?.stop();
    statusBar?.stop();
}

function _leaderboardHtml(entries: any[]): string {
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
