// src/status_bar.ts
import * as vscode from "vscode";
import { LogOracleClient } from "./client";

export class StatusBarManager {
    private item: vscode.StatusBarItem;
    private interval?: NodeJS.Timeout;

    constructor(private ctx: vscode.ExtensionContext, private client: LogOracleClient) {
        this.item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
        this.item.command = "logoracle.openChat";
        ctx.subscriptions.push(this.item);
    }

    start() {
        this.item.show();
        this._checkHealth();
        this.interval = setInterval(() => this._checkHealth(), 30_000);
    }

    stop() {
        clearInterval(this.interval);
        this.item.dispose();
    }

    updateFromCodeResult(result: any) {
        const critical = (result.issues || []).filter((i: any) => i.severity === "CRITICAL").length;
        const high     = (result.issues || []).filter((i: any) => i.severity === "HIGH").length;
        if (critical > 0) {
            this.item.text        = `$(shield) LogOracle 🔴 ${critical} CRITICAL`;
            this.item.color       = new vscode.ThemeColor("errorForeground");
            this.item.tooltip     = `${critical} critical + ${high} high issues found`;
        } else if (high > 0) {
            this.item.text        = `$(shield) LogOracle 🟠 ${high} HIGH`;
            this.item.color       = new vscode.ThemeColor("editorWarning.foreground");
        } else {
            this.item.text        = `$(shield) LogOracle 🟢 Clean`;
            this.item.color       = undefined;
        }
    }

    updateFromLogResult(result: any) {
        const critical = (result.security_findings || []).filter((f: any) => f.severity === "CRITICAL").length;
        if (critical > 0) {
            this.item.text  = `$(shield) LogOracle 🔴 ${critical} CRITICAL`;
            this.item.color = new vscode.ThemeColor("errorForeground");
        } else {
            this.item.text  = `$(shield) LogOracle 🟢 ${result.platform}/${result.distro}`;
            this.item.color = undefined;
        }
    }

    updateMode(mode: string) {
        const modeLabel = mode === "plain" ? "🌐 Plain" : "⚙️ Tech";
        this.item.tooltip = `LogOracle — ${modeLabel} mode. Click to open chat.`;
    }

    private async _checkHealth() {
        const ok = await this.client.health();
        if (!ok) {
            this.item.text    = `$(shield) LogOracle ⚪ Offline`;
            this.item.tooltip = "LogOracle backend not reachable. Start uvicorn on port 8001.";
            this.item.color   = new vscode.ThemeColor("disabledForeground");
        } else if (!this.item.text.includes("CRITICAL") && !this.item.text.includes("HIGH")) {
            this.item.text  = `$(shield) LogOracle 🟢 Ready`;
            this.item.color = undefined;
        }
    }
}
