// src/client.ts
export class LogOracleClient {
    constructor(private baseUrl: string) {}

    async analyzeCode(code: string, language: string, mode = "tech") {
        return this._post("/analyze/code", { code, language, mode });
    }

    async analyzeLog(log_text: string, redact_pii = true, mode = "tech") {
        return this._post("/analyze/log", { log_text, redact_pii, mode });
    }

    async analyzeHallucination(code: string, language: string) {
        return this._post("/analyze/hallucination", { code, language });
    }

    async chat(payload: object, sessionId: string): Promise<Response> {
        return fetch(`${this.baseUrl}/chat?session_id=${sessionId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
    }

    async ingestLogs(lines: string[], source = "vscode") {
        return this._post("/ingest/logs", { lines, source });
    }

    async getAgentStatus() {
        return this._get("/stream/agents");
    }

    async getLeaderboard() {
        return this._get("/leaderboard");
    }

    async healPreview(command: string, finding_message: string) {
        return this._post("/heal/preview", { command, finding_message });
    }

    async healApprove(token: string, dry_run = true) {
        return this._post("/heal/approve", { token, dry_run });
    }

    async health(): Promise<boolean> {
        try {
            const r = await fetch(`${this.baseUrl}/health`, { signal: AbortSignal.timeout(3000) });
            return r.ok;
        } catch { return false; }
    }

    private async _post(path: string, body: object): Promise<any> {
        const r = await fetch(`${this.baseUrl}${path}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return r.json();
    }

    private async _get(path: string): Promise<any> {
        const r = await fetch(`${this.baseUrl}${path}`);
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return r.json();
    }
}
