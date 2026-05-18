"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LogOracleClient = void 0;
// src/client.ts
class LogOracleClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
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
        return fetch(`${this.baseUrl}/chat?session_id=${sessionId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
    }
    async ingestLogs(lines, source = "vscode") {
        return this._post("/ingest/logs", { lines, source });
    }
    async getAgentStatus() {
        return this._get("/stream/agents");
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
            const r = await fetch(`${this.baseUrl}/health`, { signal: AbortSignal.timeout(3000) });
            return r.ok;
        }
        catch {
            return false;
        }
    }
    async _post(path, body) {
        const r = await fetch(`${this.baseUrl}${path}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        if (!r.ok)
            throw new Error(`${r.status} ${r.statusText}`);
        return r.json();
    }
    async _get(path) {
        const r = await fetch(`${this.baseUrl}${path}`);
        if (!r.ok)
            throw new Error(`${r.status} ${r.statusText}`);
        return r.json();
    }
}
exports.LogOracleClient = LogOracleClient;
//# sourceMappingURL=client.js.map