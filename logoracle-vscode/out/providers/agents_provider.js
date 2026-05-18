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
exports.AgentsProvider = exports.AgentItem = void 0;
// src/providers/agents_provider.ts
const vscode = __importStar(require("vscode"));
const AGENT_NAMES = ["log", "security", "performance", "hallucination", "api"];
class AgentItem extends vscode.TreeItem {
    constructor(name, status, findings) {
        super(`${name.toUpperCase()}`, vscode.TreeItemCollapsibleState.None);
        this.description = `${status} · ${findings} finding(s)`;
        this.iconPath = new vscode.ThemeIcon(status === "active" && findings > 0 ? "alert" :
            status === "active" ? "check" : "circle-outline");
        this.tooltip = `${name} agent — ${status}`;
    }
}
exports.AgentItem = AgentItem;
class AgentsProvider {
    constructor(ctx, client) {
        this.ctx = ctx;
        this.client = client;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this._agents = {};
    }
    startStream() {
        this._interval = setInterval(async () => {
            try {
                const data = await this.client.getAgentStatus();
                this._agents = data.agents || {};
                this._onDidChangeTreeData.fire();
            }
            catch { }
        }, 5000);
    }
    getTreeItem(el) { return el; }
    getChildren() {
        return AGENT_NAMES.map(name => {
            const agent = this._agents[name] || { status: "idle", findings: 0 };
            return new AgentItem(name, agent.status, agent.findings);
        });
    }
}
exports.AgentsProvider = AgentsProvider;
//# sourceMappingURL=agents_provider.js.map