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
exports.LogWatcher = void 0;
// src/log_watcher.ts
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
class LogWatcher {
    constructor(paths, client, findings, statusBar) {
        this.paths = paths;
        this.client = client;
        this.findings = findings;
        this.statusBar = statusBar;
        this.watchers = [];
        this.offsets = new Map();
        this.buffer = [];
    }
    start() {
        for (const path of this.paths) {
            try {
                // Record current file size as start offset
                const stat = fs.statSync(path);
                this.offsets.set(path, stat.size);
                const watcher = fs.watch(path, async (event) => {
                    if (event !== "change")
                        return;
                    await this._readNewLines(path);
                });
                this.watchers.push(watcher);
            }
            catch (e) {
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
    async _readNewLines(path) {
        try {
            const stat = fs.statSync(path);
            const offset = this.offsets.get(path) || 0;
            if (stat.size <= offset)
                return;
            const stream = fs.createReadStream(path, {
                start: offset,
                end: stat.size,
                encoding: "utf-8",
            });
            let data = "";
            stream.on("data", chunk => { data += chunk; });
            stream.on("end", () => {
                const lines = data.split("\n").filter(l => l.trim());
                this.buffer.push(...lines);
                this.offsets.set(path, stat.size);
            });
        }
        catch { }
    }
    async _flush() {
        if (this.buffer.length === 0)
            return;
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
                    const critical = result.security_findings.filter((f) => f.severity === "CRITICAL");
                    if (critical.length > 0) {
                        const action = await vscode.window.showErrorMessage(`LogOracle: ${critical[0].message}`, "View Fix", "Dismiss");
                        if (action === "View Fix") {
                            vscode.commands.executeCommand("logoracle.openChat");
                        }
                    }
                }
            }
        }
        catch { }
    }
}
exports.LogWatcher = LogWatcher;
//# sourceMappingURL=log_watcher.js.map