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
exports.LogOracleClient = void 0;
// src/client.ts
const vscode = __importStar(require("vscode"));
class LogOracleClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        const config = vscode.workspace.getConfiguration("logoracle");
        this.apiKey = config.get("apiKey", "");
    }
    get authHeaders() {
        const headers = {
            "Content-Type": "application/json",
        };
        if (this.apiKey) {
            headers["X-API-Key"] = this.apiKey;
        }
        return headers;
    }
    async analyzeCode(code, language, mode = "tech") {
        return this._post("/analyze/code", { code, language, mode });
    }
    async analyzeLog(log_text, redact_pii = true, mode = "tech") {
        return this._post("/analyze/log", { log_text, redact_pii, mode });
    }
    async analyzeHallucination(code, language) {
        return this._post("/analyze/hallucination", { code, language });
    }
    async chat(payload, sessionId) {
        return fetch(`${this.baseUrl}/chat/sync?session_id=${sessionId}`, {
            method: "POST",
            headers: this.authHeaders,
            body: JSON.stringify(payload),
        });
    }
    async ingestLogs(lines, source = "vscode") {
        return this._post("/ingest/logs", { lines, source });
    }
    async getAgentStatus() {
        return this._get("/agents/status");
    }
    async getLeaderboard() {
        return this._get("/leaderboard");
    }
    async healPreview(command, finding_message) {
        return this._post("/heal/preview", { command, finding_message });
    }
    async healApprove(token, dry_run = true) {
        return this._post("/heal/approve", { token, dry_run });
    }
    async health() {
        try {
            const r = await fetch(`${this.baseUrl}/health`, {
                signal: AbortSignal.timeout(3000)
            });
            return r.ok;
        }
        catch {
            return false;
        }
    }
    async _post(path, body) {
        const r = await fetch(`${this.baseUrl}${path}`, {
            method: "POST",
            headers: this.authHeaders,
            body: JSON.stringify(body),
        });
        if (!r.ok)
            throw new Error(`${r.status} ${r.statusText}`);
        return r.json();
    }
    async _get(path) {
        const r = await fetch(`${this.baseUrl}${path}`, {
            headers: this.authHeaders,
        });
        if (!r.ok)
            throw new Error(`${r.status} ${r.statusText}`);
        return r.json();
    }
}
exports.LogOracleClient = LogOracleClient;
//# sourceMappingURL=client.js.map