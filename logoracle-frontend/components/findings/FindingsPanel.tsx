"use client";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, ShieldAlert, Info, ChevronRight, Gavel } from "lucide-react";
import { useStore, Finding } from "@/store";

const SEV_CONFIG = {
  CRITICAL: { icon: ShieldAlert, color: "text-oracle-danger", border: "border-oracle-danger/40", bg: "bg-oracle-danger/5" },
  HIGH:     { icon: AlertTriangle, color: "text-oracle-warn",  border: "border-oracle-warn/40",  bg: "bg-oracle-warn/5"  },
  WARNING:  { icon: AlertTriangle, color: "text-oracle-warn",  border: "border-oracle-warn/40",  bg: "bg-oracle-warn/5"  },
  MEDIUM:   { icon: AlertTriangle, color: "text-yellow-400",   border: "border-yellow-400/40",  bg: "bg-yellow-400/5"   },
  LOW:      { icon: Info,          color: "text-oracle-info",  border: "border-oracle-info/40",  bg: "bg-oracle-info/5"  },
  INFO:     { icon: Info,          color: "text-oracle-info",  border: "border-oracle-info/40",  bg: "bg-oracle-info/5"  },
};

function FindingCard({ finding }: { finding: Finding }) {
  const { setDisputeFindingId } = useStore();
  const cfg = SEV_CONFIG[finding.severity] || SEV_CONFIG.INFO;
  const Icon = cfg.icon;

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      className={`rounded-lg border p-3 ${cfg.border} ${cfg.bg} mb-2`}
    >
      <div className="flex items-start gap-2">
        <Icon size={14} className={`mt-0.5 flex-shrink-0 ${cfg.color}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-mono font-semibold ${cfg.color}`}>{finding.severity}</span>
            <span className="text-xs text-oracle-subtext">{finding.agent}</span>
            <span className="ml-auto text-xs text-oracle-subtext font-mono">
              {Math.round(finding.confidence * 100)}%
            </span>
          </div>
          <p className="text-xs text-oracle-text leading-relaxed">{finding.message}</p>
          {finding.fix && (
            <p className="text-xs text-oracle-subtext mt-1 font-mono truncate">{finding.fix}</p>
          )}
          {finding.cve_id && (
            <a
              href={`https://nvd.nist.gov/vuln/detail/${finding.cve_id}`}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-oracle-accent underline mt-1 inline-block"
            >
              {finding.cve_id} ↗
            </a>
          )}
        </div>
      </div>
      {finding.finding_id && (
        <button
          onClick={() => setDisputeFindingId(finding.finding_id!)}
          className="mt-2 flex items-center gap-1 text-xs text-oracle-subtext
                     hover:text-oracle-warn transition-colors"
        >
          <Gavel size={11} /> Dispute
        </button>
      )}
    </motion.div>
  );
}

export default function FindingsPanel() {
  const { findings, clearFindings } = useStore();

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-oracle-border">
        <span className="text-xs font-mono text-oracle-subtext uppercase tracking-wider">
          Findings ({findings.length})
        </span>
        {findings.length > 0 && (
          <button
            onClick={clearFindings}
            className="text-xs text-oracle-subtext hover:text-oracle-danger transition-colors"
          >
            clear
          </button>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-3">
        <AnimatePresence>
          {findings.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-32 text-oracle-subtext">
              <ChevronRight size={20} className="mb-2 opacity-30" />
              <p className="text-xs">No findings yet</p>
            </div>
          ) : (
            findings.map((f, i) => <FindingCard key={f.finding_id || i} finding={f} />)
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
