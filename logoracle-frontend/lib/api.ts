const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

async function postJSON(path: string, body: unknown) {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${path} failed: ${r.status}`);
  return r.json();
}

async function getJSON(path: string) {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${path} failed: ${r.status}`);
  return r.json();
}

export async function healthCheck() {
  return getJSON("/health");
}

export async function analyzeLog(log_text: string, redact_pii = true, mode: "tech" | "plain" = "tech") {
  return postJSON("/analyze/log", { log_text, redact_pii, mode });
}

export async function analyzeCode(code: string, language: string, mode: "tech" | "plain" = "tech") {
  return postJSON("/analyze/code", { code, language, mode });
}

export async function analyzeHallucination(code: string, language: string, mode: "tech" | "plain" = "tech", filename?: string) {
  return postJSON("/analyze/hallucination", { code, language, mode, filename });
}

export function streamAgents(onEvent: (event: any) => void) {
  const es = new EventSource(`${BASE}/stream/agents`);
  es.onmessage = (event) => onEvent(JSON.parse(event.data));
  return es;
}

export function streamLogs(onLine: (event: any) => void) {
  const es = new EventSource(`${BASE}/stream/logs`);
  es.onmessage = (event) => onLine(JSON.parse(event.data));
  return es;
}

export function streamPerformance(onEvent: (event: any) => void) {
  const es = new EventSource(`${BASE}/stream/performance`);
  es.onmessage = (event) => onEvent(JSON.parse(event.data));
  return es;
}

export async function correlate(findings: any[], log_text = "") {
  return postJSON("/analyze/correlate", { findings, log_text });
}

export async function healPreview(command: string, finding_message = "", severity = "CRITICAL") {
  return postJSON("/heal/preview", { command, finding_message, severity });
}

export async function getBlockOptions(ip: string, platform = "linux", distro = "ubuntu") {
  return postJSON("/heal/block-options", { ip, platform, distro });
}

export async function healApprove(token: string, dry_run = true, agent_id?: string) {
  return postJSON("/heal/approve", { token, dry_run, agent_id });
}

export async function getHealRelayAgents() {
  return getJSON("/heal/relay/agents");
}

export async function getHealRelayStatus(token: string) {
  return getJSON(`/heal/relay/status/${token}`);
}

export async function shareSession(payload: object) {
  return postJSON("/session/share", payload);
}

export async function getLeaderboard() {
  return getJSON("/leaderboard");
}

export async function updateLeaderboard(developer_id: string, name: string, xp_delta: number, action: string) {
  return postJSON("/leaderboard/update", { developer_id, name, xp_delta, action });
}

export async function scheduleQuiz(developer_id: string, question_id: string, correct: boolean, time_seconds: number) {
  return postJSON("/quiz/schedule", { developer_id, question_id, correct, time_seconds });
}

export async function checkStreak(developer_id: string, name: string) {
  return postJSON("/streak/check", { developer_id, name });
}

export async function getBadgeEvents(since = 0) {
  return getJSON(`/badges/events?since=${since}`);
}

export async function getFixConfig() {
  return getJSON("/analyze/fix/config");
}

export async function exportPDF(payload: object) {
  const r = await fetch(`${BASE}/export/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(`PDF export failed: ${r.status}`);
  return r.blob();
}

export function streamChat(
  payload: {
    message: string;
    persona: string;
    mode: string;
    session_id?: string;
    session_context: object;
    dispute_finding_id?: string;
  },
  sessionId: string,
  onToken: (t: string) => void,
  onDone: (meta: object) => void,
  onWarning: (w: string) => void,
  onError: (e: string) => void,
  signal?: AbortSignal
) {
  fetch(`${BASE}/chat?session_id=${sessionId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...payload, session_id: payload.session_id || sessionId }),
    signal,
  }).then(async (res) => {
    const reader = res.body!.getReader();
    const dec = new TextDecoder();
    let buf = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop()!;
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const d = JSON.parse(line.slice(6));
          if (d.type === "token") onToken(d.token);
          else if (d.type === "done" || d.type === "complete") onDone(d);
          else if (d.type === "predictive_warning") onWarning(d.warning);
          else if (d.type === "error") onError(d.message);
        } catch {}
      }
    }
  }).catch((e) => { if (e.name !== "AbortError") onError(e.message); });
}

export async function generateQuiz(bug_description: string, language: string) {
  return postJSON("/quiz/generate", { bug_description, language });
}

export async function submitQuizAnswer(
  question_id: string,
  selected_index: number,
  time_taken_seconds: number
) {
  return postJSON("/quiz/answer", { question_id, selected_index, time_taken_seconds });
}
