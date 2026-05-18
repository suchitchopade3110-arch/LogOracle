import { create } from "zustand";

export type Severity = "CRITICAL" | "HIGH" | "WARNING" | "MEDIUM" | "LOW" | "INFO";
export type Persona = "default" | "architect" | "security" | "perf" | "mentor";

export interface Finding {
  agent: string;
  severity: Severity;
  message: string;
  confidence: number;
  fix?: string;
  finding_id?: string;
  cve_id?: string;
  source_ip?: string;
}

export interface FixCommand {
  platform: string;
  distro?: string;
  command: string;
  description: string;
  confidence: string;
  warning?: string;
  powershell: boolean;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
  persona?: Persona;
  intent?: string;
  xp?: number;
  warning?: string;
  disputeResult?: object;
}

export interface XPState {
  total: number;
  badges: string[];
  recentGain: number | null;
}

interface LogOracleStore {
  // Session
  sessionId: string;

  // Agent status
  agentsActive: boolean;
  setAgentsActive: (v: boolean) => void;
  agentStream: EventSource | null;
  setAgentStream: (s: EventSource | null) => void;
  logStream: EventSource | null;
  setLogStream: (s: EventSource | null) => void;
  healthBadge: "green" | "orange" | "red";
  setHealthBadge: (h: "green" | "orange" | "red") => void;
  liveLogLines: string[];
  addLiveLogLine: (line: string) => void;
  clearLiveLogLines: () => void;
  perfSnapshot: object | null;
  setPerfSnapshot: (s: object | null) => void;
  rootCause: object | null;
  setRootCause: (r: object | null) => void;
  healPending: object | null;
  setHealPending: (h: object | null) => void;
  leaderboard: object[];
  setLeaderboard: (l: object[]) => void;

  // Findings from log analysis
  findings: Finding[];
  setFindings: (f: Finding[]) => void;
  addFinding: (f: Finding) => void;
  clearFindings: () => void;

  // Fix commands
  fixes: FixCommand[];
  setFixes: (f: FixCommand[]) => void;

  // Log analysis result
  logResult: object | null;
  setLogResult: (r: object | null) => void;

  // Code analysis result
  codeResult: object | null;
  setCodeResult: (r: object | null) => void;

  // Hallucination result
  hallucinationResult: object | null;
  setHallucinationResult: (r: object | null) => void;

  // Chat
  chatMessages: ChatMessage[];
  addChatMessage: (m: ChatMessage) => void;
  updateLastMessage: (updater: (m: ChatMessage) => ChatMessage) => void;
  clearChat: () => void;
  persona: Persona;
  setPersona: (p: Persona) => void;
  mode: "tech" | "plain";
  setMode: (m: "tech" | "plain") => void;
  disputeFindingId: string | null;
  setDisputeFindingId: (id: string | null) => void;

  // XP
  xp: XPState;
  addXP: (amount: number) => void;

  // Popups / warnings
  activePopup: string | null;
  setActivePopup: (msg: string | null) => void;

  // Quiz
  quizActive: boolean;
  setQuizActive: (v: boolean) => void;
  quizData: object | null;
  setQuizData: (d: object | null) => void;
}

export const useStore = create<LogOracleStore>((set) => ({
  sessionId: `session_${Date.now()}`,

  agentsActive: false,
  setAgentsActive: (v) => set({ agentsActive: v }),
  agentStream: null,
  setAgentStream: (stream) => set({ agentStream: stream }),
  logStream: null,
  setLogStream: (stream) => set({ logStream: stream }),
  healthBadge: "green",
  setHealthBadge: (healthBadge) => set({ healthBadge }),
  liveLogLines: [],
  addLiveLogLine: (line) => set((s) => ({ liveLogLines: [...s.liveLogLines.slice(-199), line] })),
  clearLiveLogLines: () => set({ liveLogLines: [] }),
  perfSnapshot: null,
  setPerfSnapshot: (perfSnapshot) => set({ perfSnapshot }),
  rootCause: null,
  setRootCause: (rootCause) => set({ rootCause }),
  healPending: null,
  setHealPending: (healPending) => set({ healPending }),
  leaderboard: [],
  setLeaderboard: (leaderboard) => set({ leaderboard }),

  findings: [],
  setFindings: (f) => set({ findings: f }),
  addFinding: (f) => set((s) => ({ findings: [...s.findings, f] })),
  clearFindings: () => set({ findings: [] }),

  fixes: [],
  setFixes: (f) => set({ fixes: f }),

  logResult: null,
  setLogResult: (r) => set({ logResult: r }),

  codeResult: null,
  setCodeResult: (r) => set({ codeResult: r }),

  hallucinationResult: null,
  setHallucinationResult: (r) => set({ hallucinationResult: r }),

  chatMessages: [],
  addChatMessage: (m) => set((s) => ({ chatMessages: [...s.chatMessages, m] })),
  updateLastMessage: (updater) =>
    set((s) => ({
      chatMessages: s.chatMessages.map((m, i) =>
        i === s.chatMessages.length - 1 ? updater(m) : m
      ),
    })),
  clearChat: () => set({ chatMessages: [] }),
  persona: "default",
  setPersona: (p) => set({ persona: p }),
  mode: typeof window !== "undefined" ? ((localStorage.getItem("logoracle_mode") as "tech" | "plain") || "tech") : "tech",
  setMode: (m) => {
    if (typeof window !== "undefined") localStorage.setItem("logoracle_mode", m);
    set({ mode: m });
  },
  disputeFindingId: null,
  setDisputeFindingId: (id) => set({ disputeFindingId: id }),

  xp: { total: 0, badges: [], recentGain: null },
  addXP: (amount) =>
    set((s) => ({
      xp: { ...s.xp, total: s.xp.total + amount, recentGain: amount },
    })),

  activePopup: null,
  setActivePopup: (msg) => set({ activePopup: msg }),

  quizActive: false,
  setQuizActive: (v) => set({ quizActive: v }),
  quizData: null,
  setQuizData: (d) => set({ quizData: d }),
}));
