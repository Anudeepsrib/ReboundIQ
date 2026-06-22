import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "sonner";
import { Providers } from "./providers";
import {
  BarChart3,
  Bot,
  BriefcaseBusiness,
  FileSearch,
  FileText,
  Gauge,
  LockKeyhole,
  MessagesSquare,
  ShieldCheck,
  Trophy,
} from "lucide-react";

export const metadata: Metadata = {
  title: "ReboundIQ - Layoff-to-Offer AI Copilot",
  description: "Privacy-first, local-first AI career recovery OS. From layoff to offer with structured execution.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const navItems = [
    { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
    { href: "/runway", label: "Runway", icon: Gauge },
    { href: "/resume", label: "Resume", icon: FileText },
    { href: "/jobs", label: "JD Match", icon: FileSearch },
    { href: "/applications", label: "Applications", icon: BriefcaseBusiness },
    { href: "/proof", label: "Proof", icon: Trophy },
    { href: "/interview", label: "Interview", icon: MessagesSquare },
    { href: "/campaigns", label: "Campaigns", icon: Bot },
    { href: "/settings/ai-providers", label: "AI", icon: ShieldCheck },
    { href: "/settings/privacy", label: "Privacy", icon: LockKeyhole },
  ];

  return (
    <html lang="en" className="dark">
      <body className="bg-zinc-950 text-zinc-200">
        <div className="min-h-screen flex flex-col">
          <nav className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex flex-col gap-3 xl:min-h-16 xl:flex-row xl:items-center xl:justify-between">
              <div className="flex items-center gap-3">
                <div className="font-semibold tracking-tight text-xl">ReboundIQ</div>
                <div className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-900">LOCAL FIRST</div>
              </div>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-sm text-zinc-300">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <a key={item.href} href={item.href} className="inline-flex items-center gap-1.5 hover:text-white">
                      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
                      {item.label}
                    </a>
                  );
                })}
              </div>
              <div className="text-xs text-zinc-500">Demo • Local Ollama</div>
            </div>
          </nav>
          <Providers>
            <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 py-8">
              {children}
            </main>
          </Providers>
          <footer className="text-center text-[10px] text-zinc-600 py-4 border-t border-zinc-900">
            Planning guidance only. Not legal, financial, immigration, or tax advice. All outputs must be reviewed and edited by you. • Local AI default • Data stays yours
          </footer>
        </div>
        <Toaster position="top-center" richColors closeButton />
      </body>
    </html>
  );
}
