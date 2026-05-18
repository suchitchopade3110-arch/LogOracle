"use client";
import { motion } from "framer-motion";
import { Shield, Activity, Cpu, Eye, Zap } from "lucide-react";
import { useStore } from "@/store";

const AGENTS = [
  { id: "log",           label: "Log",       icon: Activity, color: "#00E5FF" },
  { id: "security",      label: "Security",  icon: Shield,   color: "#FF3B5C" },
  { id: "performance",   label: "Perf",      icon: Zap,      color: "#FF6B35" },
  { id: "hallucination", label: "Halluc.",   icon: Eye,      color: "#4D9FFF" },
  { id: "api",           label: "API",       icon: Cpu,      color: "#00D97E" },
];

export default function AgentStatusBar() {
  const { agentsActive, findings } = useStore();

  const criticalCount = findings.filter((f) => f.severity === "CRITICAL").length;

  return (
    <div className="flex items-center gap-2 px-4 py-2 bg-oracle-surface border-b border-oracle-border">
      <span className="text-xs text-oracle-subtext font-mono mr-2">AGENTS</span>
      {AGENTS.map(({ id, label, icon: Icon, color }) => {
        const hasFindings = findings.some((f) => f.agent === id);
        return (
          <motion.div
            key={id}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs font-mono
              border transition-all
              ${agentsActive
                ? hasFindings
                  ? "border-oracle-danger/40 bg-oracle-danger/5 text-oracle-danger"
                  : "border-oracle-accent/20 bg-oracle-accent/5 text-oracle-accent"
                : "border-oracle-border text-oracle-subtext"
              }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${agentsActive ? "agent-pulse" : ""}`}
              style={{ background: agentsActive ? color : "#2A3045" }}
            />
            <Icon size={11} />
            <span className="hidden sm:inline">{label}</span>
          </motion.div>
        );
      })}
      {criticalCount > 0 && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="ml-auto flex items-center gap-1.5 px-2 py-1 rounded
                     bg-oracle-danger/10 border border-oracle-danger/30 text-oracle-danger text-xs font-mono"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-oracle-danger agent-pulse" />
          {criticalCount} CRITICAL
        </motion.div>
      )}
    </div>
  );
}
