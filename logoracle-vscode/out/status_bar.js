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
exports.StatusBarManager = void 0;
// src/status_bar.ts
const vscode = __importStar(require("vscode"));
class StatusBarManager {
    constructor(ctx, client) {
        this.ctx = ctx;
        this.client = client;
        this.item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
        this.item.command = "logoracle.openChat";
        ctx.subscriptions.push(this.item);
    }
    start() {
        this.item.show();
        this._checkHealth();
        this.interval = setInterval(() => this._checkHealth(), 30000);
    }
    stop() {
        clearInterval(this.interval);
        this.item.dispose();
    }
    updateFromCodeResult(result) {
        const critical = (result.issues || []).filter((i) => i.severity === "CRITICAL").length;
        const high = (result.issues || []).filter((i) => i.severity === "HIGH").length;
        if (critical > 0) {
            this.item.text = `$(shield) LogOracle 🔴 ${critical} CRITICAL`;
            this.item.color = new vscode.ThemeColor("errorForeground");
            this.item.tooltip = `${critical} critical + ${high} high issues found`;
        }
        else if (high > 0) {
            this.item.text = `$(shield) LogOracle 🟠 ${high} HIGH`;
            this.item.color = new vscode.ThemeColor("editorWarning.foreground");
        }
        else {
            this.item.text = `$(shield) LogOracle 🟢 Clean`;
            this.item.color = undefined;
        }
    }
    updateFromLogResult(result) {
        const critical = (result.security_findings || []).filter((f) => f.severity === "CRITICAL").length;
        if (critical > 0) {
            this.item.text = `$(shield) LogOracle 🔴 ${critical} CRITICAL`;
            this.item.color = new vscode.ThemeColor("errorForeground");
        }
        else {
            this.item.text = `$(shield) LogOracle 🟢 ${result.platform}/${result.distro}`;
            this.item.color = undefined;
        }
    }
    updateMode(mode) {
        const modeLabel = mode === "plain" ? "🌐 Plain" : "⚙️ Tech";
        this.item.tooltip = `LogOracle — ${modeLabel} mode. Click to open chat.`;
    }
    async _checkHealth() {
        const ok = await this.client.health();
        if (!ok) {
            this.item.text = `$(shield) LogOracle ⚪ Offline`;
            this.item.tooltip = "LogOracle backend not reachable. Start uvicorn on port 8001.";
            this.item.color = new vscode.ThemeColor("disabledForeground");
        }
        else if (!this.item.text.includes("CRITICAL") && !this.item.text.includes("HIGH")) {
            this.item.text = `$(shield) LogOracle 🟢 Ready`;
            this.item.color = undefined;
        }
    }
}
exports.StatusBarManager = StatusBarManager;
//# sourceMappingURL=status_bar.js.map