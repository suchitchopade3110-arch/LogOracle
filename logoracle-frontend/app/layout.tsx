import type { Metadata } from "next";
import "@/styles/globals.css";
import Sidebar from "@/components/layout/Sidebar";

export const metadata: Metadata = {
  title: "LogOracle",
  description: "AI Antivirus for Code. AI Doctor for Applications.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="scan-overlay" />
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <main className="flex-1 ml-16 lg:ml-56 overflow-hidden flex flex-col bg-oracle-bg">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
