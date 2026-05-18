// src/log_watcher.ts
import * as vscode from "vscode";
import * as fs from "fs";
import { LogOracleClient } from "./client";
import { FindingsProvider } from "./providers/findings_provider";
import { StatusBarManager } from "./status_bar";

export class LogWatcher {
    private watchers: fs.FSWatcher[]   = [];
    private offsets:  Map<string, number> = new Map();
    private buffer:   string[]         = [];
    private flushInterval?: NodeJS.Timeout;

    constructor(
        private paths: string[],
        private client: LogOracleClient,
        private findings: FindingsProvider,
        private statusBar: StatusBarManager,
    ) {}

    start() {
        for (const path of this.paths) {
            try {
                // Record current file size as start offset
                const stat = fs.statSync(path);
                this.offsets.set(path, stat.size);

                const watcher = fs.watch(path, async (event) => {
                    if (event !== "change") return;
                    await this._readNewLines(path);
                });
                this.watchers.push(watcher);
            } catch (e) {
                vscode.window.showWarningMessage(`LogOracle: Cannot watch ${path} — ${e}`);
            }
        }

        // Flush buffer every 2s to backend
        this.flushInterval = setInterval(() => this._flush(), 2000);
    }

    stop() {
        this.watchers.forEach(w => w.close());
        this.watchers = [];
        clearInterval(this.flushInterval);
    }

    private async _readNewLines(path: string) {
        try {
            const stat      = fs.statSync(path);
            const offset    = this.offsets.get(path) || 0;
            if (stat.size <= offset) return;

            const stream = fs.createReadStream(path, {
                start:    offset,
                end:      stat.size,
                encoding: "utf-8",
            });

            let data = "";
            stream.on("data", chunk => { data += chunk; });
            stream.on("end", () => {
                const lines = data.split("\n").filter(l => l.trim());
                this.buffer.push(...lines);
                this.offsets.set(path, stat.size);
            });
        } catch {}
    }

    private async _flush() {
        if (this.buffer.length === 0) return;

        const lines = [...this.buffer];
        this.buffer = [];

        try {
            // Send to backend log stream
            await this.client.ingestLogs(lines, "vscode-watcher");

            // Also analyze for security findings if 10+ lines accumulated
            if (lines.length >= 10) {
                const result = await this.client.analyzeLog(lines.join("\n"), true, "tech");
                if (result.security_findings?.length > 0) {
                    this.findings.updateLogFindings(result.security_findings);
                    this.statusBar.updateFromLogResult(result);

                    // Show VS Code notification for CRITICAL findings
                    const critical = result.security_findings.filter((f: any) => f.severity === "CRITICAL");
                    if (critical.length > 0) {
                        const action = await vscode.window.showErrorMessage(
                            `LogOracle: ${critical[0].message}`,
                            "View Fix", "Dismiss"
                        );
                        if (action === "View Fix") {
                            vscode.commands.executeCommand("logoracle.openChat");
                        }
                    }
                }
            }
        } catch {}
    }
}
