"use client";
import { useState } from "react";
import { Download, Share2 } from "lucide-react";
import { exportPDF, shareSession } from "@/lib/api";
import { useStore } from "@/store";

export default function ExportPage() {
  const { sessionId, findings, fixes, rootCause, logResult, codeResult, xp } = useStore();
  const [shareUrl, setShareUrl] = useState("");
  const [status, setStatus] = useState("");

  const payload = {
    session_id: sessionId,
    findings,
    fixes,
    root_cause: rootCause,
    platform: (logResult as any)?.platform || "unknown",
    distro: (logResult as any)?.distro,
    log_snippet: ((logResult as any)?.events || []).map((e: any) => e.raw).join("\n"),
    code_issues: (codeResult as any)?.issues || [],
  };

  const downloadPDF = async () => {
    setStatus("Exporting...");
    const blob = await exportPDF(payload);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `logoracle-${sessionId}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
    setStatus("PDF exported");
  };

  const share = async () => {
    const res = await shareSession(payload);
    const url = `${window.location.origin}${res.share_url}`;
    setShareUrl(url);
    await navigator.clipboard?.writeText(url).catch(() => {});
    setStatus("Share URL copied");
  };

  return (
    <div className="h-full overflow-y-auto p-6 max-w-3xl">
      <h1 className="text-xl font-display font-bold text-oracle-text mb-2">Export Session</h1>
      <p className="text-sm text-oracle-subtext mb-6">Package the current debug session for handoff.</p>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        {[
          ["Platform", payload.platform],
          ["Distro", payload.distro || "unknown"],
          ["Findings", findings.length],
          ["XP Earned", xp.total],
        ].map(([label, value]) => (
          <div key={label} className="rounded-xl bg-oracle-surface border border-oracle-border p-4">
            <p className="text-xs text-oracle-subtext font-mono mb-1">{label}</p>
            <p className="text-lg text-oracle-accent font-mono">{value}</p>
          </div>
        ))}
      </div>

      <div className="flex gap-3 mb-4">
        <button
          onClick={downloadPDF}
          className="inline-flex items-center gap-2 rounded-lg border border-oracle-accent/30 bg-oracle-accent/10 px-4 py-2 text-sm text-oracle-accent"
        >
          <Download size={15} /> Export PDF
        </button>
        <button
          onClick={share}
          className="inline-flex items-center gap-2 rounded-lg border border-oracle-border bg-oracle-surface px-4 py-2 text-sm text-oracle-text"
        >
          <Share2 size={15} /> Share Session
        </button>
      </div>

      {status && <p className="text-xs text-oracle-success mb-3">{status}</p>}
      {shareUrl && (
        <code className="block rounded-lg border border-oracle-border bg-oracle-surface p-3 text-xs text-oracle-accent break-all">
          {shareUrl}
        </code>
      )}
    </div>
  );
}
