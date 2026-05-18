"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { Upload, Play, Terminal, AlertTriangle, GitBranch, Wrench } from "lucide-react";
import AgentStatusBar from "@/components/agents/AgentStatusBar";
import FindingsPanel from "@/components/findings/FindingsPanel";
import { useStore } from "@/store";
import { analyzeLog, correlate, healPreview } from "@/lib/api";

export default function AnalyzePage() {
  const { mode, findings, setFindings, setFixes, setLogResult, setRootCause, setHealPending } = useStore();
  const [logText, setLogText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  const run = async () => {
    if (!logText.trim()) return;
    setLoading(true); setError("");
    try {
      const res = await analyzeLog(logText, true, mode);
      setResult(res);
      setLogResult(res);
      if (res.security_findings) {
        setFindings(res.security_findings.map((f: any) => ({
          agent: f.agent || "security",
          severity: f.severity,
          message: f.message,
          confidence: f.confidence || 0.9,
          fix: f.fix_linux || f.fix,
          finding_id: f.cve_id || undefined,
          cve_id: f.cve_id,
          source_ip: f.source_ip,
        })));
      }
      if (res.fixes) setFixes(res.fixes);
    } catch (e: any) {
      setError(e.message || "Failed to analyze");
    } finally {
      setLoading(false);
    }
  };

  const runCorrelate = async () => {
    const res = await correlate(findings, logText);
    setRootCause(res);
  };

  const previewHeal = async (fix: any) => {
    const res = await healPreview(fix.command, fix.description || "LogOracle finding");
    setHealPending({ ...res, command: fix.command });
  };

  const DEMO = `Apr 10 12:00:01 host sshd[1234]: Failed password for root from 203.0.113.42 port 22 ssh2
Apr 10 12:00:02 host sshd[1234]: Failed password for root from 203.0.113.42 port 22 ssh2
Apr 10 12:00:03 host sshd[1234]: Failed password for root from 203.0.113.42 port 22 ssh2
Apr 10 12:00:04 host sshd[1234]: Failed password for root from 203.0.113.42 port 22 ssh2
Apr 10 12:00:05 host sshd[1234]: Failed password for root from 203.0.113.42 port 22 ssh2
Apr 10 12:00:06 host kernel: Out of memory: Kill process 999 (nginx) score 900`;

  return (
    <div className="flex flex-col h-full">
      <AgentStatusBar />
      <div className="flex-1 overflow-hidden grid grid-cols-1 lg:grid-cols-2 gap-0">

        {/* Input */}
        <div className="border-r border-oracle-border flex flex-col">
          <div className="px-4 py-3 border-b border-oracle-border flex items-center gap-3">
            <Terminal size={15} className="text-oracle-accent" />
            <span className="text-sm font-display font-semibold text-oracle-text">Log Input</span>
            <button onClick={() => setLogText(DEMO)}
              className="ml-auto text-xs text-oracle-subtext hover:text-oracle-accent transition-colors">
              load demo
            </button>
          </div>
          <textarea
            value={logText}
            onChange={(e) => setLogText(e.target.value)}
            placeholder="Paste syslog, auth.log, dmesg, Windows Event Log, macOS unified log..."
            className="flex-1 bg-transparent p-4 text-xs font-mono text-oracle-text
                       placeholder-oracle-subtext resize-none focus:outline-none"
          />
          <div className="p-3 border-t border-oracle-border flex gap-2">
            <button
              onClick={run}
              disabled={loading || !logText.trim()}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-mono
                         bg-oracle-accent/10 border border-oracle-accent/30 text-oracle-accent
                         hover:bg-oracle-accent/20 transition-colors disabled:opacity-30"
            >
              {loading ? (
                <span className="w-3 h-3 border border-oracle-accent/50 border-t-oracle-accent rounded-full animate-spin" />
              ) : (
                <Play size={13} />
              )}
              {loading ? "Analyzing..." : "Analyze"}
            </button>
            {error && <p className="text-xs text-oracle-danger flex items-center gap-1"><AlertTriangle size={11} />{error}</p>}
          </div>
        </div>

        {/* Results */}
        <div className="flex flex-col overflow-hidden">
          {result ? (
            <>
              {/* Meta */}
              <div className="px-4 py-3 border-b border-oracle-border grid grid-cols-3 gap-3">
                {[
                  ["Platform", result.platform],
                  ["Distro", result.distro || "unknown"],
                  ["Format", result.format_detected],
                  ["Mode", result.mode || mode],
                  ["Chunks", result.chunk_count || 1],
                  ["Lines", result.total_lines || result.event_count],
                ].map(([k, v]) => (
                  <div key={k}>
                    <p className="text-xs text-oracle-subtext font-mono">{k}</p>
                    <p className="text-sm font-mono text-oracle-accent">{v}</p>
                  </div>
                ))}
              </div>

              {result.pii_detected && (
                <div className="px-4 py-2 border-b border-oracle-border text-xs text-oracle-warn bg-oracle-warn/5">
                  ⚠ {result.pii_banner || "PII detected and redacted before display."}
                </div>
              )}

              {result.chunked && (
                <div className="px-4 py-2 border-b border-oracle-border text-xs text-oracle-subtext">
                  Large log chunked into <span className="text-oracle-accent">{result.chunk_count}</span> analysis chunks.
                </div>
              )}

              {/* Fix commands */}
              {result.fixes?.length > 0 && (
                <div className="px-4 py-3 border-b border-oracle-border">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs text-oracle-subtext font-mono">FIX COMMANDS</p>
                    <button onClick={runCorrelate} className="flex items-center gap-1 text-xs text-oracle-accent hover:text-oracle-text">
                      <GitBranch size={12} /> Correlate
                    </button>
                  </div>
                  {result.fixes.map((fix: any, i: number) => (
                    <div key={i} className="mb-2 rounded-lg bg-oracle-surface border border-oracle-border p-2">
                      <p className="text-xs text-oracle-subtext mb-1">{fix.description} · {fix.platform}/{fix.distro || "any"}</p>
                      <code className="text-xs text-oracle-accent font-mono block whitespace-pre-wrap">{fix.command}</code>
                      {fix.warning && <p className="text-xs text-oracle-warn mt-1">⚠ {fix.warning}</p>}
                      <button
                        onClick={() => previewHeal(fix)}
                        className="mt-2 inline-flex items-center gap-1 text-xs px-2 py-1 rounded border border-oracle-accent/30 text-oracle-accent bg-oracle-accent/5"
                      >
                        <Wrench size={11} /> Heal Preview
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <div className="flex-1 overflow-hidden">
                <FindingsPanel />
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-oracle-subtext">
              <Upload size={32} className="mb-3 opacity-20" />
              <p className="text-sm">Paste logs and click Analyze</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
