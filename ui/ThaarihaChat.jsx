import { useState, useRef, useEffect, useCallback } from "react";

const PERSONAS = [
  { id: "default", label: "Assistant", icon: "ti-cpu" },
  { id: "architect", label: "Architect", icon: "ti-vector-triangle" },
  { id: "security", label: "Security", icon: "ti-shield-lock" },
  { id: "perf", label: "Performance", icon: "ti-gauge" },
  { id: "mentor", label: "Mentor", icon: "ti-school" },
];

const XP_COLORS = {
  0: "var(--color-text-secondary)",
  10: "#639922",
  15: "#639922",
  20: "#185FA5",
  60: "#B85F00",
};

function XPBadge({ xp }) {
  if (xp == null) return null;
  const color = XP_COLORS[xp] || XP_COLORS[20];
  return (
    <span style={{
      fontSize: 11, fontWeight: 500, padding: "2px 7px",
      borderRadius: 99, border: `0.5px solid ${color}`,
      color, marginLeft: 8, display: "inline-block"
    }}>+{xp} XP</span>
  );
}

function IntentBadge({ intent }) {
  if (!intent || intent === "general") return null;
  const map = {
    dispute: ["ti-gavel", "#993C1D"],
    plain_english: ["ti-text-size", "#185FA5"],
    clarify: ["ti-help-circle", "#3B6D11"],
    accept: ["ti-circle-check", "#0F6E56"],
  };
  const [icon, color] = map[intent] || ["ti-tag", "var(--color-text-secondary)"];
  return (
    <span style={{ fontSize: 11, color, marginLeft: 6, display: "inline-flex", alignItems: "center", gap: 3 }}>
      <i className={`ti ${icon}`} style={{ fontSize: 12 }} aria-hidden="true" />
      {intent.replace("_", " ")}
    </span>
  );
}

function WarningBanner({ warning }) {
  if (!warning) return null;
  return (
    <div style={{
      margin: "8px 0", padding: "8px 12px",
      background: "var(--color-background-warning)",
      border: "0.5px solid var(--color-border-warning)",
      borderRadius: "var(--border-radius-md)",
      fontSize: 13, color: "var(--color-text-warning)",
      display: "flex", alignItems: "flex-start", gap: 8
    }}>
      <i className="ti ti-alert-triangle" style={{ fontSize: 16, flexShrink: 0, marginTop: 1 }} aria-hidden="true" />
      <span>{warning}</span>
    </div>
  );
}

function DisputeResult({ result }) {
  if (!result) return null;
  const retracted = result.verdict === "retracted";
  return (
    <div style={{
      marginTop: 8, padding: "8px 12px",
      background: retracted ? "var(--color-background-success)" : "var(--color-background-danger)",
      border: `0.5px solid ${retracted ? "var(--color-border-success)" : "var(--color-border-danger)"}`,
      borderRadius: "var(--border-radius-md)",
      fontSize: 12, color: retracted ? "var(--color-text-success)" : "var(--color-text-danger)"
    }}>
      <strong>{retracted ? "✓ Retracted" : "✗ Confirmed"}</strong>
      {" · "}{result.new_severity} · {Math.round((result.new_confidence || 0) * 100)}% confidence
    </div>
  );
}

function Message({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div style={{
      display: "flex", flexDirection: "column",
      alignItems: isUser ? "flex-end" : "flex-start",
      marginBottom: 16
    }}>
      {!isUser && (
        <div style={{ fontSize: 11, color: "var(--color-text-secondary)", marginBottom: 4, display: "flex", alignItems: "center" }}>
          <i className={`ti ${PERSONAS.find(p => p.id === (msg.persona || "default"))?.icon || "ti-cpu"}`}
             style={{ fontSize: 13, marginRight: 4 }} aria-hidden="true" />
          {PERSONAS.find(p => p.id === (msg.persona || "default"))?.label || "Assistant"}
          <IntentBadge intent={msg.intent} />
          <XPBadge xp={msg.xp} />
        </div>
      )}
      <div style={{
        maxWidth: "82%",
        padding: "10px 14px",
        borderRadius: isUser ? "16px 16px 4px 16px" : "4px 16px 16px 16px",
        background: isUser ? "var(--color-background-info)" : "var(--color-background-secondary)",
        border: "0.5px solid var(--color-border-tertiary)",
        fontSize: 14, lineHeight: 1.6,
        color: isUser ? "var(--color-text-info)" : "var(--color-text-primary)",
        whiteSpace: "pre-wrap", wordBreak: "break-word"
      }}>
        {msg.content}
        {msg.streaming && (
          <span style={{ display: "inline-block", width: 2, height: 14, background: "var(--color-text-primary)", marginLeft: 2, animation: "blink 1s step-end infinite", verticalAlign: "middle" }} />
        )}
      </div>
      <WarningBanner warning={msg.warning} />
      <DisputeResult result={msg.disputeResult} />
    </div>
  );
}

function FindingChip({ finding, onDispute }) {
  const colors = { CRITICAL: "#A32D2D", HIGH: "#993C1D", MEDIUM: "#854F0B", LOW: "#3B6D11", INFO: "#185FA5" };
  const color = colors[finding.severity] || colors.INFO;
  return (
    <div style={{
      padding: "8px 12px", marginBottom: 6,
      background: "var(--color-background-secondary)",
      border: "0.5px solid var(--color-border-tertiary)",
      borderRadius: "var(--border-radius-md)",
      fontSize: 13
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
        <span style={{ fontSize: 11, fontWeight: 500, padding: "1px 6px", borderRadius: 4, background: `${color}18`, color }}>{finding.severity}</span>
        <span style={{ fontWeight: 500, color: "var(--color-text-primary)" }}>{finding.agent}</span>
        <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--color-text-secondary)" }}>{Math.round(finding.confidence * 100)}%</span>
      </div>
      <p style={{ margin: "0 0 6px", color: "var(--color-text-secondary)", lineHeight: 1.4 }}>{finding.message}</p>
      {finding.fix && <p style={{ margin: "0 0 6px", fontSize: 12, color: "var(--color-text-tertiary)" }}>Fix: {finding.fix}</p>}
      <button onClick={() => onDispute(finding)} style={{ fontSize: 12, padding: "3px 10px", cursor: "pointer" }}>
        <i className="ti ti-gavel" style={{ fontSize: 12, marginRight: 4 }} aria-hidden="true" />
        Dispute
      </button>
    </div>
  );
}

function scenarioFindings(result) {
  if (!result) return [];

  if (Array.isArray(result.security_findings)) {
    return result.security_findings.map((f, index) => ({
      agent: f.agent || "security",
      severity: f.severity || "INFO",
      message: f.message || "Security finding",
      confidence: f.confidence ?? 0.85,
      fix: f.fix || f.fix_linux || f.fix_windows,
      finding_id: `demo_security_${index}`,
    }));
  }

  if (Array.isArray(result.issues)) {
    return result.issues.map((issue, index) => ({
      agent: issue.pass_number ? `pass${issue.pass_number}` : "analysis",
      severity: issue.severity || "INFO",
      message: issue.message || "Code issue",
      confidence: issue.confidence ?? 0.85,
      fix: issue.fix_hint,
      finding_id: `demo_issue_${index}`,
    }));
  }

  if (Array.isArray(result.items)) {
    return result.items
      .filter(item => item.status !== "valid")
      .map((item, index) => ({
        agent: "hallucination",
        severity: item.status === "hallucinated" ? "HIGH" : "MEDIUM",
        message: `${item.name} is ${item.status} in ${item.registry}`,
        confidence: 0.82,
        fix: item.suggestion,
        finding_id: `demo_hallucination_${index}`,
      }));
  }

  if (typeof result.flagged === "boolean") {
    return [{
      agent: "intent",
      severity: result.severity || (result.flagged ? "HIGH" : "INFO"),
      message: result.explanation || result.message || "Intent gap analysis completed",
      confidence: result.confidence ?? 0.8,
      finding_id: "demo_intent_0",
    }];
  }

  return [];
}

function summarizeScenarioRun(scenario, result) {
  if (!scenario) return "Demo scenario completed.";
  if (scenario.endpoint === "/analyze/log") {
    return `${scenario.title}\nPlatform: ${result.platform}/${result.distro || "unknown"}\nEvents: ${result.event_count}\nFindings: ${result.security_findings?.length || 0}\nFixes: ${result.fixes?.length || 0}`;
  }
  if (scenario.endpoint === "/analyze/code") {
    return `${scenario.title}\nPass 1 issues: ${result.pass1_count || 0}\nPass 3 issues: ${result.pass3_count || 0}`;
  }
  if (scenario.endpoint === "/analyze/hallucination") {
    return `${scenario.title}\nValid: ${result.valid_count || 0}\nDeprecated: ${result.deprecated_count || 0}\nHallucinated: ${result.hallucinated_count || 0}`;
  }
  return `${scenario.title}\n${JSON.stringify(result, null, 2)}`;
}

export default function ThaarihaChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [persona, setPersona] = useState("default");
  const [mode, setMode] = useState("tech");
  const [loading, setLoading] = useState(false);
  const [backendUrl, setBackendUrl] = useState("http://127.0.0.1:8001");
  const [showConfig, setShowConfig] = useState(false);
  const [scenarios, setScenarios] = useState([]);
  const [demoLoading, setDemoLoading] = useState(null);
  const [findings, setFindings] = useState([
    { agent: "security", severity: "HIGH", message: "SQL injection risk in user input handler", confidence: 0.88, fix: "Use parameterized queries", finding_id: "sec001" },
    { agent: "perf", severity: "MEDIUM", message: "Missing index on users.email causing full table scan", confidence: 0.92, fix: "CREATE INDEX idx_users_email ON users(email)", finding_id: "perf001" }
  ]);
  const [disputeId, setDisputeId] = useState(null);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const bottomRef = useRef(null);
  const abortRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    let cancelled = false;
    fetch(`${backendUrl}/demo/scenarios`)
      .then(res => res.ok ? res.json() : Promise.reject(new Error(`Server error ${res.status}`)))
      .then(data => {
        if (!cancelled) setScenarios(data.scenarios || []);
      })
      .catch(() => {
        if (!cancelled) setScenarios([]);
      });
    return () => { cancelled = true; };
  }, [backendUrl]);

  const handleDispute = useCallback((finding) => {
    setDisputeId(finding.finding_id);
    setInput(`I dispute this finding — "${finding.message.slice(0, 60)}..."`);
  }, []);

  const runDemo = useCallback(async (scenario) => {
    if (demoLoading) return;
    setDemoLoading(scenario.scenario_id);
    try {
      const res = await fetch(`${backendUrl}/demo/run/${scenario.scenario_id}`, { method: "POST" });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();
      const result = data.result || {};
      const demoFindings = scenarioFindings(result);
      setFindings(demoFindings);
      setInput(data.scenario?.chat_prompt || scenario.chat_prompt || "");
      setMessages(prev => [...prev, {
        id: Date.now(),
        role: "assistant",
        content: summarizeScenarioRun(data.scenario || scenario, result),
        persona: "default",
        intent: "general",
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now(),
        role: "assistant",
        content: `Demo failed: ${err.message}`,
        persona: "default",
      }]);
    } finally {
      setDemoLoading(null);
    }
  }, [backendUrl, demoLoading]);

  const sendMessage = useCallback(async () => {
    if (!input.trim() || loading) return;

    const userMsg = { role: "user", content: input.trim() };
    setMessages(prev => [...prev, userMsg]);
    const userText = input.trim();
    setInput("");
    setLoading(true);

    const botMsgId = Date.now();
    setMessages(prev => [...prev, { id: botMsgId, role: "assistant", content: "", streaming: true, persona }]);

    const payload = {
      message: userText,
      persona,
      mode,
      dispute_finding_id: disputeId || undefined,
      session_context: {
        findings,
        last_log_lines: "",
        code_diff: "",
        chat_history: [],
        developer_profile: { expertise_level: "intermediate", past_quiz_scores: [], badges: [] }
      }
    };

    setDisputeId(null);

    try {
      abortRef.current = new AbortController();
      const res = await fetch(`${backendUrl}/chat?session_id=${sessionId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: abortRef.current.signal
      });

      if (!res.ok) throw new Error(`Server error ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(line.slice(6));

            if (data.type === "token") {
              setMessages(prev => prev.map(m =>
                m.id === botMsgId ? { ...m, content: m.content + data.token } : m
              ));
            } else if (data.type === "predictive_warning") {
              setMessages(prev => prev.map(m =>
                m.id === botMsgId ? { ...m, warning: data.warning } : m
              ));
            } else if (data.type === "complete") {
              setMessages(prev => prev.map(m =>
                m.id === botMsgId ? {
                  ...m, content: data.reply, streaming: false,
                  intent: data.intent, xp: data.xp_awarded,
                  disputeResult: data.dispute_result
                } : m
              ));
            } else if (data.type === "done") {
              setMessages(prev => prev.map(m =>
                m.id === botMsgId ? { ...m, streaming: false, intent: data.intent } : m
              ));
            } else if (data.type === "error") {
              setMessages(prev => prev.map(m =>
                m.id === botMsgId ? { ...m, content: `Error: ${data.message}`, streaming: false } : m
              ));
            }
          } catch {}
        }
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        setMessages(prev => prev.map(m =>
          m.id === botMsgId
            ? { ...m, content: `Connection failed. Is the backend running at ${backendUrl}?\n\n${err.message}`, streaming: false }
            : m
        ));
      }
    } finally {
      setLoading(false);
      setMessages(prev => prev.map(m => m.id === botMsgId ? { ...m, streaming: false } : m));
    }
  }, [input, loading, persona, mode, findings, backendUrl, sessionId, disputeId]);

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  return (
    <div style={{ display: "flex", height: "100vh", fontFamily: "var(--font-sans)", background: "var(--color-background-tertiary)" }}>
      <style>{`@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }`}</style>

      {/* sidebar */}
      <div style={{
        width: 220, flexShrink: 0, borderRight: "0.5px solid var(--color-border-tertiary)",
        background: "var(--color-background-primary)", display: "flex", flexDirection: "column", padding: "16px 12px"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 24 }}>
          <i className="ti ti-terminal-2" style={{ fontSize: 20, color: "var(--color-text-primary)" }} aria-hidden="true" />
          <span style={{ fontWeight: 500, fontSize: 15 }}>Thaariha</span>
        </div>

        <p style={{ fontSize: 11, color: "var(--color-text-secondary)", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.06em" }}>Persona</p>
        {PERSONAS.map(p => (
          <button key={p.id} onClick={() => setPersona(p.id)} style={{
            display: "flex", alignItems: "center", gap: 8, width: "100%",
            padding: "7px 10px", marginBottom: 2, cursor: "pointer",
            borderRadius: "var(--border-radius-md)",
            background: persona === p.id ? "var(--color-background-secondary)" : "transparent",
            border: persona === p.id ? "0.5px solid var(--color-border-secondary)" : "0.5px solid transparent",
            color: "var(--color-text-primary)", fontSize: 13, textAlign: "left"
          }}>
            <i className={`ti ${p.icon}`} style={{ fontSize: 16, color: persona === p.id ? "var(--color-text-info)" : "var(--color-text-secondary)" }} aria-hidden="true" />
            {p.label}
          </button>
        ))}

        <div style={{ marginTop: 16, marginBottom: 8 }}>
          <p style={{ fontSize: 11, color: "var(--color-text-secondary)", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.06em" }}>Mode</p>
          <div style={{ display: "flex", gap: 4 }}>
            {["tech", "plain"].map(m => (
              <button key={m} onClick={() => setMode(m)} style={{
                flex: 1, padding: "5px 0", cursor: "pointer", fontSize: 12,
                borderRadius: "var(--border-radius-md)",
                background: mode === m ? "var(--color-background-info)" : "var(--color-background-secondary)",
                border: `0.5px solid ${mode === m ? "var(--color-border-info)" : "var(--color-border-tertiary)"}`,
                color: mode === m ? "var(--color-text-info)" : "var(--color-text-secondary)"
              }}>{m}</button>
            ))}
          </div>
        </div>

        <div style={{ flex: 1 }} />

        <button onClick={() => setShowConfig(s => !s)} style={{
          display: "flex", alignItems: "center", gap: 6, fontSize: 12,
          color: "var(--color-text-secondary)", padding: "6px 0", cursor: "pointer",
          background: "none", border: "none"
        }}>
          <i className="ti ti-settings" style={{ fontSize: 14 }} aria-hidden="true" />
          Backend config
        </button>
        {showConfig && (
          <div style={{ marginTop: 6 }}>
            <input
              value={backendUrl}
              onChange={e => setBackendUrl(e.target.value)}
              placeholder="http://127.0.0.1:8001"
              style={{ width: "100%", fontSize: 12, padding: "5px 8px", boxSizing: "border-box" }}
            />
            <p style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginTop: 4 }}>
              Run: <code style={{ fontSize: 11 }}>uvicorn main:app --port 8001</code>
            </p>
          </div>
        )}
      </div>

      {/* main */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>

        {/* demo scenarios */}
        <div style={{
          borderBottom: "0.5px solid var(--color-border-tertiary)",
          background: "var(--color-background-primary)",
          padding: "10px 20px",
          display: "flex",
          alignItems: "center",
          gap: 8,
          overflowX: "auto",
          minHeight: 48
        }}>
          <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-secondary)", flexShrink: 0 }}>
            <i className="ti ti-player-play" style={{ fontSize: 13, marginRight: 5 }} aria-hidden="true" />
            Demos
          </span>
          {scenarios.length === 0 && (
            <span style={{ fontSize: 12, color: "var(--color-text-tertiary)" }}>No scenarios loaded</span>
          )}
          {scenarios.map(s => (
            <button
              key={s.scenario_id}
              onClick={() => runDemo(s)}
              disabled={!!demoLoading}
              title={`${s.severity} · ${s.category}`}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 5,
                flexShrink: 0,
                padding: "5px 9px",
                cursor: demoLoading ? "default" : "pointer",
                borderRadius: "var(--border-radius-md)",
                border: "0.5px solid var(--color-border-tertiary)",
                background: demoLoading === s.scenario_id ? "var(--color-background-info)" : "var(--color-background-secondary)",
                color: demoLoading === s.scenario_id ? "var(--color-text-info)" : "var(--color-text-primary)",
                fontSize: 12
              }}
            >
              <i className={`ti ${demoLoading === s.scenario_id ? "ti-loader-2" : "ti-bolt"}`} style={{ fontSize: 13 }} aria-hidden="true" />
              {s.scenario_id.slice(0, 2)} {s.title.replace(/^(SSH|DOM) /, "")}
            </button>
          ))}
        </div>

        {/* findings panel */}
        <div style={{
          borderBottom: "0.5px solid var(--color-border-tertiary)",
          background: "var(--color-background-primary)",
          padding: "10px 20px"
        }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
            <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-secondary)" }}>
              <i className="ti ti-list-details" style={{ fontSize: 13, marginRight: 5 }} aria-hidden="true" />
              Active findings ({findings.length})
            </span>
            <button onClick={() => setFindings([])} style={{ fontSize: 11, color: "var(--color-text-tertiary)", background: "none", border: "none", cursor: "pointer" }}>
              clear all
            </button>
          </div>
          {findings.length === 0 && (
            <p style={{ fontSize: 12, color: "var(--color-text-tertiary)", margin: 0 }}>No findings. Add via session context.</p>
          )}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {findings.map(f => (
              <FindingChip key={f.finding_id} finding={f} onDispute={handleDispute} />
            ))}
          </div>
        </div>

        {/* messages */}
        <div style={{ flex: 1, overflowY: "auto", padding: "20px 24px" }}>
          {messages.length === 0 && (
            <div style={{ textAlign: "center", marginTop: 60, color: "var(--color-text-secondary)" }}>
              <i className="ti ti-terminal-2" style={{ fontSize: 40, display: "block", marginBottom: 12 }} aria-hidden="true" />
              <p style={{ fontSize: 15, fontWeight: 500, color: "var(--color-text-primary)", marginBottom: 6 }}>Thaariha Chatbot</p>
              <p style={{ fontSize: 13 }}>Select a persona and start debugging</p>
              <p style={{ fontSize: 12, marginTop: 16, color: "var(--color-text-tertiary)" }}>
                Backend: <code style={{ fontSize: 12 }}>{backendUrl}</code>
              </p>
            </div>
          )}
          {messages.map((msg, i) => <Message key={msg.id || i} msg={msg} />)}
          {disputeId && (
            <div style={{ fontSize: 12, color: "var(--color-text-warning)", marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
              <i className="ti ti-gavel" style={{ fontSize: 13 }} aria-hidden="true" />
              Disputing finding <code style={{ fontSize: 11 }}>{disputeId}</code>
              <button onClick={() => setDisputeId(null)} style={{ fontSize: 11, color: "var(--color-text-tertiary)", background: "none", border: "none", cursor: "pointer", marginLeft: 4 }}>cancel</button>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* input */}
        <div style={{
          borderTop: "0.5px solid var(--color-border-tertiary)",
          background: "var(--color-background-primary)",
          padding: "12px 20px",
          display: "flex", gap: 10, alignItems: "flex-end"
        }}>
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder={disputeId ? `Disputing ${disputeId}…` : "Ask the assistant…"}
            rows={1}
            style={{
              flex: 1, resize: "none", fontSize: 14, padding: "8px 12px",
              borderRadius: "var(--border-radius-md)",
              border: "0.5px solid var(--color-border-secondary)",
              background: "var(--color-background-secondary)",
              color: "var(--color-text-primary)", lineHeight: 1.5, maxHeight: 120,
              overflowY: "auto", outline: "none", fontFamily: "var(--font-sans)"
            }}
          />
          <button
            onClick={loading ? () => abortRef.current?.abort() : sendMessage}
            disabled={!loading && !input.trim()}
            style={{
              padding: "8px 16px", cursor: loading || input.trim() ? "pointer" : "default",
              borderRadius: "var(--border-radius-md)",
              background: loading ? "var(--color-background-danger)" : "var(--color-background-info)",
              border: `0.5px solid ${loading ? "var(--color-border-danger)" : "var(--color-border-info)"}`,
              color: loading ? "var(--color-text-danger)" : "var(--color-text-info)",
              fontSize: 14, display: "flex", alignItems: "center", gap: 6
            }}
          >
            <i className={`ti ${loading ? "ti-player-stop" : "ti-send"}`} style={{ fontSize: 15 }} aria-hidden="true" />
            {loading ? "Stop" : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}
