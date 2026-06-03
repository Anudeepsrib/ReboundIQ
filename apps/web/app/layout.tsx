import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "ReboundIQ - Layoff-to-Offer AI Copilot",
  description: "Privacy-first, local-first AI career recovery OS. From layoff to offer with structured execution.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-zinc-950 text-zinc-200">
        <div className="min-h-screen flex flex-col">
          <nav className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="font-semibold tracking-tight text-xl">ReboundIQ</div>
                <div className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-900">LOCAL FIRST</div>
              </div>
              <div className="flex items-center gap-6 text-sm">
                <a href="/dashboard" className="hover:text-white">Dashboard</a>
                <a href="/resume" className="hover:text-white">Resume</a>
                <a href="/jobs" className="hover:text-white">JD Match</a>
                <a href="/campaigns" className="hover:text-white">Campaigns</a>
                <a href="/settings/ai-providers" className="hover:text-white">AI Settings</a>
                <a href="/settings/privacy" className="hover:text-white">Privacy</a>
              </div>
              <div className="text-xs text-zinc-500">Demo • Local Ollama</div>
            </div>
          </nav>
          <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8">
            {children}
          </main>
          <footer className="text-center text-[10px] text-zinc-600 py-4 border-t border-zinc-900">
            Planning guidance only. Not legal, financial, immigration, or tax advice. All outputs must be reviewed and edited by you. • Local AI default • Data stays yours
          </footer>
        </div>
        <Toaster position="top-center" richColors closeButton />
      </body>
    </html>
  );
}
