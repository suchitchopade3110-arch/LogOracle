"use client";
import { useEffect } from "react";
import AgentStatusBar from "@/components/agents/AgentStatusBar";
import ChatPanel from "@/components/chat/ChatPanel";
import { streamLogs } from "@/lib/api";
import { useStore } from "@/store";

export default function ChatPage() {
  const { findings, persona, liveLogLines, addLiveLogLine, setLogStream } = useStore();

  useEffect(() => {
    const es = streamLogs((event) => {
      if (event.line) addLiveLogLine(event.line);
    });
    setLogStream(es);
    return () => es.close();
  }, [addLiveLogLine, setLogStream]);

  return (
    <div className="flex flex-col h-full">
      <AgentStatusBar />
      <div className="px-4 py-2 border-b border-oracle-border text-xs text-oracle-subtext font-mono">
        {liveLogLines.length} log lines · {findings.length} findings · {persona} persona
      </div>
      <div className="flex-1 overflow-hidden grid grid-cols-1 lg:grid-cols-3">
        <div className="lg:col-span-2 overflow-hidden border-r border-oracle-border">
          <ChatPanel />
        </div>
        <div className="hidden lg:flex flex-col overflow-hidden">
          <div className="px-3 py-2 border-b border-oracle-border text-xs text-oracle-subtext font-mono">
            Live Logs
          </div>
          <div className="flex-1 overflow-y-auto p-3 font-mono text-xs text-oracle-subtext space-y-1">
            {liveLogLines.length === 0 ? (
              <p>No log stream yet</p>
            ) : liveLogLines.slice(-120).map((line, i) => (
              <p key={i} className="whitespace-pre-wrap">{line}</p>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
