"use client";
import { useStore } from "@/store";

export default function ModeToggle() {
  const { mode, setMode } = useStore();

  return (
    <div className="hidden lg:block px-3 py-3 border-t border-oracle-border">
      <p className="text-xs text-oracle-subtext font-mono mb-2">MODE</p>
      <div className="grid grid-cols-2 gap-1 rounded-lg bg-oracle-border/30 p-1">
        {([
          ["tech", "⚙️ Tech"],
          ["plain", "🌐 Plain"],
        ] as const).map(([value, label]) => (
          <button
            key={value}
            onClick={() => setMode(value)}
            className={`text-xs rounded-md py-1.5 font-mono transition-colors ${
              mode === value
                ? "bg-oracle-accent/15 text-oracle-accent border border-oracle-accent/30"
                : "text-oracle-subtext hover:text-oracle-text border border-transparent"
            }`}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
