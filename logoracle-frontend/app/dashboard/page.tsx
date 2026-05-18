"use client";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import ReactFlow from "reactflow";
import "reactflow/dist/style.css";
import { Activity, Shield, Code2, Zap, CheckCircle, XCircle, X } from "lucide-react";
import AgentStatusBar from "@/components/agents/AgentStatusBar";
import FindingsPanel from "@/components/findings/FindingsPanel";
import ChatPanel from "@/components/chat/ChatPanel";
import { useStore } from "@/store";
import {
  correlate,
  getHealRelayAgents,
  getHealRelayStatus,
  healApprove,
  healthCheck,
  streamAgents,
  streamPerformance,
} from "@/lib/api";

function StatCard({ label, value, icon: Icon, color }: { label: string; value: string | number; icon: any; color: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-oracle-surface border border-oracle-border rounded-xl p-4"
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-oracle-subtext font-mono uppercase">{label}</span>
        <Icon size={14} style={{ color }} />
      </div>
      <p className="text-2xl font-display font-bold" style={{ color }}>{value}</p>
    </motion.div>
  );
}

export default function DashboardPage() {
  const {
    findings, setFindings, xp, setAgentsActive, agentsActive,
    setHealthBadge, healthBadge, setPerfSnapshot, rootCause, setRootCause,
    healPending, setHealPending,
  } = useStore();
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [popup, setPopup] = useState<string | null>(null);
  const [relayAgents, setRelayAgents] = useState<any[]>([]);
  const [selectedAgent, setSelectedAgent] = useState("");

  useEffect(() => {
    healthCheck()
      .then(() => { setBackendOk(true); setAgentsActive(true); })
      .catch(() => setBackendOk(false));

    getHealRelayAgents()
      .then((res) => {
        const agents = res.agents || [];
        setRelayAgents(agents);
        if (agents[0]?.agent_id) setSelectedAgent(agents[0].agent_id);
      })
      .catch(() => {});
  }, [setAgentsActive]);

  useEffect(() => {
    let lastPopup = 0;
    const es = streamAgents((event) => {
      setAgentsActive(true);
      setHealthBadge(event.health_badge || event.health || "green");
      const allFindings = Object.values(event.agents || {})
        .flatMap((agent: any) => agent.findings_list || []);
      if (allFindings.length) setFindings(allFindings as any);
      const critical = event.critical || allFindings.filter((f: any) => f.severity === "CRITICAL").length;
      if (critical > 0 && Date.now() - lastPopup > 300000) {
        lastPopup = Date.now();
        setPopup(event.agents?.security?.last_event || "Critical finding detected");
      }
    });
    const perf = streamPerformance((event) => setPerfSnapshot(event.snapshot || event));
    return () => { es.close(); perf.close(); };
  }, [setAgentsActive, setFindings, setHealthBadge, setPerfSnapshot]);

  useEffect(() => {
    if (!findings.length) return;
    correlate(findings, "").then(setRootCause).catch(() => {});
  }, [findings, setRootCause]);

  const critical = findings.filter((f) => f.severity === "CRITICAL").length;
  const warnings = findings.filter((f) => f.severity === "WARNING").length;

  return (
    <div className="flex flex-col h-full">
      <AgentStatusBar />

      <div className="flex-1 overflow-hidden grid grid-cols-1 lg:grid-cols-3 gap-0">
        {/* Left: stats + findings */}
        <div className="lg:col-span-1 border-r border-oracle-border flex flex-col">
          {/* Backend status */}
          <div className="px-4 py-3 border-b border-oracle-border flex items-center gap-2">
            {backendOk === null && <span className="text-xs text-oracle-subtext">Connecting...</span>}
            {backendOk === true && (
              <><CheckCircle size={13} className="text-oracle-success" />
              <span className="text-xs text-oracle-success font-mono">Backend online</span></>
            )}
            {backendOk === false && (
              <><XCircle size={13} className="text-oracle-danger" />
              <span className="text-xs text-oracle-danger font-mono">Backend offline — start uvicorn</span></>
            )}
            <span className={`ml-auto text-xs font-mono px-2 py-0.5 rounded-full border ${
              healthBadge === "red" ? "text-oracle-danger border-oracle-danger/40 bg-oracle-danger/10" :
              healthBadge === "orange" ? "text-oracle-warn border-oracle-warn/40 bg-oracle-warn/10" :
              "text-oracle-success border-oracle-success/40 bg-oracle-success/10"
            }`}>
              {healthBadge.toUpperCase()}
            </span>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-2 p-3 border-b border-oracle-border">
            <StatCard label="Critical"  value={critical}    icon={Shield}   color="#FF3B5C" />
            <StatCard label="Warnings"  value={warnings}    icon={Activity} color="#FF6B35" />
            <StatCard label="XP Total"  value={xp.total}    icon={Zap}      color="#00E5FF" />
            <StatCard label="Badges"    value={xp.badges.length} icon={Code2} color="#00D97E" />
          </div>

          {/* Findings */}
          <div className="flex-1 overflow-hidden">
            <FindingsPanel />
          </div>
        </div>

        {/* Right: Chat */}
        <div className="lg:col-span-2 flex flex-col overflow-hidden">
          <div className="px-4 py-3 border-b border-oracle-border">
            <h2 className="text-sm font-display font-semibold text-oracle-text">AI Assistant</h2>
            <p className="text-xs text-oracle-subtext mt-0.5">Ask about findings, disputes, explanations</p>
          </div>
          <div className="flex-1 overflow-hidden">
            {popup && (
              <div className="m-3 rounded-xl border border-oracle-danger/40 bg-oracle-danger/10 p-3 text-sm text-oracle-danger flex gap-2">
                <Shield size={15} />
                <span className="flex-1">{popup}</span>
                <button onClick={() => setPopup(null)}><X size={14} /></button>
              </div>
            )}
            {healPending && (
              <div className="m-3 rounded-xl border border-oracle-accent/30 bg-oracle-accent/5 p-3">
                <p className="text-xs text-oracle-subtext font-mono mb-1">SELF-HEAL APPROVAL</p>
                <code className="block text-xs text-oracle-accent mb-2">{(healPending as any).command}</code>
                {relayAgents.length > 0 && (
                  <select
                    value={selectedAgent}
                    onChange={(e) => setSelectedAgent(e.target.value)}
                    className="mb-2 w-full rounded border border-oracle-border bg-oracle-bg px-2 py-1 text-xs text-oracle-text"
                  >
                    <option value="">Local dry run</option>
                    {relayAgents.map((agent) => (
                      <option key={agent.agent_id} value={agent.agent_id}>
                        {agent.agent_id} ({agent.status})
                      </option>
                    ))}
                  </select>
                )}
                <button
                  onClick={async () => {
                    const token = (healPending as any).token;
                    const res = await healApprove(token, !selectedAgent, selectedAgent || undefined);
                    if (res.relay) {
                      setTimeout(async () => {
                        const status = await getHealRelayStatus(token).catch(() => null);
                        alert(status?.message || status?.status || res.message);
                      }, 1500);
                    } else {
                      alert(res.message || "Approved");
                    }
                    setHealPending(null);
                  }}
                  className="text-xs px-3 py-1 rounded bg-oracle-accent/10 border border-oracle-accent/30 text-oracle-accent"
                >
                  {selectedAgent ? "Approve on agent" : "Approve dry run"}
                </button>
              </div>
            )}
            {rootCause && (rootCause as any).nodes?.length > 0 && (
              <div className="m-3 h-56 rounded-xl border border-oracle-border bg-oracle-surface overflow-hidden">
                <div className="px-3 py-2 border-b border-oracle-border text-xs text-oracle-subtext font-mono">
                  Root Cause Chain
                </div>
                <ReactFlow
                  nodes={(rootCause as any).nodes}
                  edges={(rootCause as any).edges || []}
                  fitView
                  proOptions={{ hideAttribution: true }}
                />
              </div>
            )}
            <ChatPanel />
          </div>
        </div>
      </div>
    </div>
  );
}
