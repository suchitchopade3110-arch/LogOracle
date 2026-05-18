// src/providers/agents_provider.ts
import * as vscode from "vscode";
import { LogOracleClient } from "../client";

const AGENT_NAMES = ["log", "security", "performance", "hallucination", "api"];

export class AgentItem extends vscode.TreeItem {
    constructor(name: string, status: string, findings: number) {
        super(`${name.toUpperCase()}`, vscode.TreeItemCollapsibleState.None);
        this.description = `${status} · ${findings} finding(s)`;
        this.iconPath    = new vscode.ThemeIcon(
            status === "active" && findings > 0 ? "alert" :
            status === "active" ? "check" : "circle-outline"
        );
        this.tooltip = `${name} agent — ${status}`;
    }
}

export class AgentsProvider implements vscode.TreeDataProvider<AgentItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<void>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    private _agents: Record<string, any> = {};
    private _interval?: NodeJS.Timeout;

    constructor(private ctx: vscode.ExtensionContext, private client: LogOracleClient) {}

    startStream() {
        this._interval = setInterval(async () => {
            try {
                const data = await this.client.getAgentStatus();
                this._agents = data.agents || {};
                this._onDidChangeTreeData.fire();
            } catch {}
        }, 5000);
    }

    getTreeItem(el: AgentItem) { return el; }

    getChildren(): AgentItem[] {
        return AGENT_NAMES.map(name => {
            const agent = this._agents[name] || { status: "idle", findings: 0 };
            return new AgentItem(name, agent.status, agent.findings);
        });
    }
}
