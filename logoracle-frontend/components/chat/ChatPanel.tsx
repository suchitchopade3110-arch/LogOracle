"use client";
import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Square, Bot, User } from "lucide-react";
import { useStore, ChatMessage, Persona } from "@/store";
import { streamChat } from "@/lib/api";

const PERSONAS: { id: Persona; label: string }[] = [
  { id: "default",   label: "Assistant" },
  { id: "architect", label: "Architect" },
  { id: "security",  label: "Security"  },
  { id: "perf",      label: "Perf"      },
  { id: "mentor",    label: "Mentor"    },
];

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 mb-4 ${isUser ? "flex-row-reverse" : ""}`}
    >
      <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0
        ${isUser ? "bg-oracle-accent/20" : "bg-oracle-surface border border-oracle-border"}`}>
        {isUser ? <User size={13} className="text-oracle-accent" /> : <Bot size={13} className="text-oracle-subtext" />}
      </div>
      <div className={`max-w-[80%] rounded-xl px-3 py-2.5 text-sm leading-relaxed
        ${isUser
          ? "bg-oracle-accent/10 border border-oracle-accent/20 text-oracle-text"
          : "bg-oracle-surface border border-oracle-border text-oracle-text"
        } ${msg.streaming ? "stream-cursor" : ""}`}
      >
        <p className="whitespace-pre-wrap">{msg.content}</p>
        {msg.warning && (
          <div className="mt-2 text-xs text-oracle-warn border-t border-oracle-border pt-2">
            ⚠ {msg.warning}
          </div>
        )}
        {msg.xp != null && msg.xp > 0 && (
          <div className="mt-1 text-xs text-oracle-success">+{msg.xp} XP</div>
        )}
        {msg.intent && msg.intent !== "general" && (
          <div className="mt-1 text-xs text-oracle-subtext font-mono">[{msg.intent}]</div>
        )}
      </div>
    </motion.div>
  );
}

export default function ChatPanel() {
  const {
    chatMessages, addChatMessage, updateLastMessage, clearChat,
    persona, setPersona, mode, setMode,
    sessionId, findings, liveLogLines, disputeFindingId, setDisputeFindingId,
    addXP,
  } = useStore();

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  useEffect(() => {
    if (disputeFindingId) {
      const f = findings.find((x) => x.finding_id === disputeFindingId);
      if (f) setInput(`I dispute this finding — "${f.message.slice(0, 60)}..."`);
    }
  }, [disputeFindingId]);

  const send = () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput("");

    const userMsg: ChatMessage = { id: Date.now().toString(), role: "user", content: text };
    addChatMessage(userMsg);

    const botId = (Date.now() + 1).toString();
    addChatMessage({ id: botId, role: "assistant", content: "", streaming: true, persona });
    setLoading(true);

    abortRef.current = new AbortController();

    streamChat(
      {
        message: text,
        persona,
        mode,
        dispute_finding_id: disputeFindingId || undefined,
        session_context: {
          findings,
          last_log_lines: liveLogLines.slice(-500).join("\n"),
          code_diff: "",
          chat_history: [],
          developer_profile: { expertise_level: "intermediate", past_quiz_scores: [], badges: [] },
        },
      },
      sessionId,
      (token) => updateLastMessage((m) => ({ ...m, content: m.content + token })),
      (meta: any) => {
        updateLastMessage((m) => ({
          ...m, streaming: false,
          intent: meta.intent,
          xp: meta.xp_awarded,
          disputeResult: meta.dispute_result,
        }));
        if (meta.xp_awarded) addXP(meta.xp_awarded);
        setLoading(false);
        setDisputeFindingId(null);
      },
      (warning) => updateLastMessage((m) => ({ ...m, warning })),
      (err) => {
        updateLastMessage((m) => ({ ...m, content: `Error: ${err}`, streaming: false }));
        setLoading(false);
      },
      abortRef.current.signal,
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-oracle-border flex-wrap">
        {PERSONAS.map((p) => (
          <button
            key={p.id}
            onClick={() => setPersona(p.id)}
            className={`text-xs px-2.5 py-1 rounded font-mono transition-colors
              ${persona === p.id
                ? "bg-oracle-accent/10 text-oracle-accent border border-oracle-accent/30"
                : "text-oracle-subtext hover:text-oracle-text border border-transparent"
              }`}
          >
            {p.label}
          </button>
        ))}
        <div className="ml-auto flex gap-1">
          {(["tech", "plain"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`text-xs px-2 py-1 rounded transition-colors
                ${mode === m ? "text-oracle-accent" : "text-oracle-subtext"}`}
            >
              {m}
            </button>
          ))}
          <button onClick={clearChat} className="text-xs text-oracle-subtext hover:text-oracle-danger ml-2 transition-colors">
            clear
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        {chatMessages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-oracle-subtext">
            <Bot size={32} className="mb-3 opacity-30" />
            <p className="text-sm">Ask the {persona} assistant</p>
          </div>
        )}
        <AnimatePresence>
          {chatMessages.map((m) => <MessageBubble key={m.id} msg={m} />)}
        </AnimatePresence>
        {disputeFindingId && (
          <div className="text-xs text-oracle-warn mb-2 flex items-center gap-2">
            Disputing: <code className="font-mono">{disputeFindingId}</code>
            <button onClick={() => { setDisputeFindingId(null); setInput(""); }}
              className="text-oracle-subtext hover:text-oracle-danger">cancel</button>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-oracle-border flex gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
          placeholder="Ask the assistant..."
          rows={1}
          className="flex-1 bg-oracle-border/30 border border-oracle-border rounded-lg px-3 py-2
                     text-sm text-oracle-text placeholder-oracle-subtext resize-none
                     focus:outline-none focus:border-oracle-accent/50 transition-colors font-body"
        />
        <button
          onClick={loading ? () => abortRef.current?.abort() : send}
          disabled={!loading && !input.trim()}
          className={`px-3 rounded-lg transition-colors flex items-center justify-center
            ${loading
              ? "bg-oracle-danger/10 border border-oracle-danger/30 text-oracle-danger"
              : "bg-oracle-accent/10 border border-oracle-accent/30 text-oracle-accent disabled:opacity-30"
            }`}
        >
          {loading ? <Square size={15} /> : <Send size={15} />}
        </button>
      </div>
    </div>
  );
}
