"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Terminal, Shield, Code2, MessageSquare, Trophy, Activity, Download } from "lucide-react";
import { useStore } from "@/store";
import ModeToggle from "@/components/ui/ModeToggle";

const NAV = [
  { href: "/dashboard", icon: Activity,      label: "Dashboard" },
  { href: "/analyze",   icon: Shield,        label: "Log Analysis" },
  { href: "/code",      icon: Code2,         label: "Code Intel" },
  { href: "/chat",      icon: MessageSquare, label: "AI Chat" },
  { href: "/quiz",      icon: Trophy,        label: "Growth" },
  { href: "/export",    icon: Download,      label: "Export" },
];

export default function Sidebar() {
  const path = usePathname();
  const { xp, agentsActive } = useStore();

  return (
    <aside className="fixed left-0 top-0 h-screen w-16 lg:w-56 flex flex-col
                      bg-oracle-surface border-r border-oracle-border z-50">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-oracle-border">
        <div className="relative">
          <Terminal size={22} className="text-oracle-accent" />
          {agentsActive && (
            <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-oracle-success agent-pulse" />
          )}
        </div>
        <span className="hidden lg:block font-display font-bold text-oracle-text tracking-tight">
          Log<span className="text-oracle-accent">Oracle</span>
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 flex flex-col gap-1 px-2">
        {NAV.map(({ href, icon: Icon, label }) => {
          const active = path === href || path.startsWith(href + "/");
          return (
            <Link key={href} href={href}>
              <motion.div
                whileHover={{ x: 2 }}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-colors
                  ${active
                    ? "bg-oracle-accent/10 text-oracle-accent border border-oracle-accent/20"
                    : "text-oracle-subtext hover:text-oracle-text hover:bg-oracle-border/40"
                  }`}
              >
                <Icon size={18} />
                <span className="hidden lg:block text-sm font-body">{label}</span>
              </motion.div>
            </Link>
          );
        })}
      </nav>

      <ModeToggle />

      {/* XP bar */}
      <div className="px-3 py-4 border-t border-oracle-border">
        <div className="hidden lg:block mb-1 flex justify-between text-xs text-oracle-subtext">
          <span>XP</span>
          <span className="text-oracle-accent font-mono">{xp.total}</span>
        </div>
        <div className="h-1 bg-oracle-border rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-oracle-accent rounded-full"
            animate={{ width: `${Math.min((xp.total % 100), 100)}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
        {xp.badges.length > 0 && (
          <div className="hidden lg:flex flex-wrap gap-1 mt-2">
            {xp.badges.slice(-3).map((b) => (
              <span key={b} className="text-xs px-1.5 py-0.5 rounded bg-oracle-accent/10 text-oracle-accent">
                {b}
              </span>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
