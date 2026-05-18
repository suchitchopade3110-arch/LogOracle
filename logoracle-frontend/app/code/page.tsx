"use client";
import { useState, lazy, Suspense } from "react";
import { motion } from "framer-motion";
import { Code2, Play, Shield, AlertTriangle, Info } from "lucide-react";
import AgentStatusBar from "@/components/agents/AgentStatusBar";
import { analyzeCode, analyzeHallucination, getFixConfig } from "@/lib/api";
import { useStore } from "@/store";

const MonacoEditor = lazy(() => import("@monaco-editor/react"));

const LANGS = ["python", "javascript", "typescript", "java", "csharp"];

const SEV_ICON: Record<string, any> = { CRITICAL: Shield, HIGH: AlertTriangle, MEDIUM: AlertTriangle, LOW: Info, INFO: Info };
const SEV_COLOR: Record<string, string> = {
  CRITICAL: "text-oracle-danger", HIGH: "text-oracle-warn",
  MEDIUM: "text-yellow-400", LOW: "text-oracle-info", INFO: "text-oracle-subtext",
};

const DEMO_CODE = `import os
import pickle

password = "hardcoded_secret_123"
user_input = input("Enter ID: ")
os.system("ls " + user_input)

def process(items=[]):
    try:
        data = pickle.loads(user_input)
        return items[0]
    except:
        pass
`;

export default function CodePage() {
  const { mode, setCodeResult, setHallucinationResult } = useStore();
  const [code, setCode] = useState(DEMO_CODE);
  const [lang, setLang] = useState("python");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [halluc, setHalluc] = useState<any>(null);
  const [fixConfig, setFixConfig] = useState<any>(null);
  const [tab, setTab] = useState<"issues" | "hallucination">("issues");

  const run = async () => {
    setLoading(true);
    try {
      const [codeRes, hallucRes] = await Promise.all([
        analyzeCode(code, lang, mode),
        analyzeHallucination(code, lang, mode),
      ]);
      const cfg = await getFixConfig().catch(() => null);
      setResult(codeRes);
      setHalluc(hallucRes);
      setFixConfig(cfg?.config || null);
      setCodeResult(codeRes);
      setHallucinationResult(hallucRes);
    } finally {
      setLoading(false);
    }
  };

  const score = result
    ? Math.max(0, 100 - (result.issues || []).reduce((acc: number, issue: any) => {
        const weight: any = { CRITICAL: 30, HIGH: 22, MEDIUM: 12, LOW: 6, INFO: 2 };
        return acc + (weight[issue.severity] || 5);
      }, 0))
    : 100;

  return (
    <div className="flex flex-col h-full">
      <AgentStatusBar />
      <div className="flex-1 overflow-hidden grid grid-cols-1 lg:grid-cols-2 gap-0">

        {/* Editor */}
        <div className="border-r border-oracle-border flex flex-col">
          <div className="px-4 py-3 border-b border-oracle-border flex items-center gap-3">
            <Code2 size={15} className="text-oracle-accent" />
            <span className="text-sm font-display font-semibold">Code Editor</span>
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value)}
              className="ml-auto text-xs bg-oracle-border/40 border border-oracle-border
                         text-oracle-text rounded px-2 py-1 focus:outline-none"
            >
              {LANGS.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
          <div className="flex-1 overflow-hidden">
            <Suspense fallback={<div className="flex-1 flex items-center justify-center text-oracle-subtext text-sm">Loading editor...</div>}>
              <MonacoEditor
                height="100%"
                language={lang}
                value={code}
                onChange={(v) => setCode(v || "")}
                theme="vs-dark"
                options={{
                  fontSize: 12, fontFamily: "JetBrains Mono",
                  minimap: { enabled: false }, scrollBeyondLastLine: false,
                  lineNumbers: "on", renderLineHighlight: "line",
                }}
              />
            </Suspense>
          </div>
          <div className="p-3 border-t border-oracle-border">
            <button
              onClick={run}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-mono
                         bg-oracle-accent/10 border border-oracle-accent/30 text-oracle-accent
                         hover:bg-oracle-accent/20 transition-colors disabled:opacity-30"
            >
              {loading
                ? <span className="w-3 h-3 border border-oracle-accent/50 border-t-oracle-accent rounded-full animate-spin" />
                : <Play size={13} />}
              {loading ? "Analyzing..." : "Run Analysis"}
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="flex flex-col overflow-hidden">
          {result ? (
            <>
              {/* Tabs */}
              <div className="flex border-b border-oracle-border">
                {[
                  { id: "issues", label: `Issues (${result.issues?.length || 0})` },
                  { id: "hallucination", label: `Trust (${halluc?.hallucinated_count || 0} halluc)` },
                ].map(({ id, label }) => (
                  <button
                    key={id}
                    onClick={() => setTab(id as any)}
                    className={`px-4 py-3 text-xs font-mono transition-colors border-b-2
                      ${tab === id
                        ? "border-oracle-accent text-oracle-accent"
                        : "border-transparent text-oracle-subtext hover:text-oracle-text"
                      }`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              <div className="grid grid-cols-4 gap-2 p-3 border-b border-oracle-border">
                {[
                  ["AST", result.pass1_count ?? 0],
                  ["LLM", result.pass2_count ?? "n/a"],
                  ["OWASP", result.pass3_count ?? 0],
                  ["Health", score],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-lg bg-oracle-surface border border-oracle-border p-2 text-center">
                    <p className="text-xs text-oracle-subtext font-mono">{label}</p>
                    <p className={`text-lg font-mono font-bold ${label === "Health" && Number(value) < 70 ? "text-oracle-warn" : "text-oracle-accent"}`}>{value}</p>
                  </div>
                ))}
              </div>

              <div className="flex-1 overflow-y-auto p-3">
                {tab === "issues" && (
                  <div>
                    {result.issues?.length === 0 && (
                      <p className="text-xs text-oracle-subtext text-center py-8">No issues found ✓</p>
                    )}
                    {result.issues?.map((issue: any, i: number) => {
                      const Icon = SEV_ICON[issue.severity] || Info;
                      return (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, x: -4 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.03 }}
                          className="mb-2 p-3 rounded-lg bg-oracle-surface border border-oracle-border"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <Icon size={12} className={SEV_COLOR[issue.severity]} />
                            <span className={`text-xs font-mono font-semibold ${SEV_COLOR[issue.severity]}`}>
                              {issue.severity}
                            </span>
                            {issue.line && <span className="text-xs text-oracle-subtext font-mono">L{issue.line}</span>}
                            {issue.cwe_id && <span className="text-xs text-oracle-subtext font-mono ml-auto">{issue.cwe_id}</span>}
                          </div>
                          <p className="text-xs text-oracle-text">{issue.message}</p>
                          {issue.rule_id && <p className="text-xs text-oracle-subtext font-mono mt-1">{issue.rule_id}</p>}
                          {issue.confidence >= (fixConfig?.confidence_threshold ?? 0.7) && (
                            <div className="mt-2 rounded border border-oracle-accent/20 bg-oracle-accent/5 p-2">
                              <p className="text-xs text-oracle-accent font-mono mb-1">Auto-fix diff preview</p>
                              <pre className="text-xs text-oracle-subtext whitespace-pre-wrap">
{`- vulnerable code near line ${issue.line || "?"}
+ apply safe pattern for ${issue.cwe_id || issue.rule_id || "this issue"}`}
                              </pre>
                              {fixConfig?.dry_run !== false && (
                                <p className="text-xs text-oracle-warn mt-1">Dry-run only. Approval required.</p>
                              )}
                            </div>
                          )}
                        </motion.div>
                      );
                    })}
                  </div>
                )}

                {tab === "hallucination" && halluc && (
                  <div>
                    <div className="grid grid-cols-3 gap-2 mb-3">
                      {[
                        ["Valid",       halluc.valid_count,       "text-oracle-success"],
                        ["Deprecated",  halluc.deprecated_count,  "text-oracle-warn"],
                        ["Hallucinated",halluc.hallucinated_count,"text-oracle-danger"],
                      ].map(([label, count, color]) => (
                        <div key={label as string} className="bg-oracle-surface border border-oracle-border rounded-lg p-2 text-center">
                          <p className={`text-lg font-mono font-bold ${color}`}>{count}</p>
                          <p className="text-xs text-oracle-subtext">{label}</p>
                        </div>
                      ))}
                    </div>
                    {halluc.items?.map((item: any, i: number) => (
                      <div key={i} className="flex items-center gap-3 py-2 border-b border-oracle-border">
                        <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                          item.status === "valid" ? "bg-oracle-success" :
                          item.status === "deprecated" ? "bg-oracle-warn" : "bg-oracle-danger"
                        }`} />
                        <span className="text-xs font-mono text-oracle-text">{item.name}</span>
                        <span className={`text-xs ml-auto font-mono ${
                          item.status === "valid" ? "text-oracle-success" :
                          item.status === "deprecated" ? "text-oracle-warn" : "text-oracle-danger"
                        }`}>{item.status}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-oracle-subtext">
              <Code2 size={32} className="mb-3 opacity-20" />
              <p className="text-sm">Click Run Analysis to scan your code</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
