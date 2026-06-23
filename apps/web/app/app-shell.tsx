'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart3,
  Bot,
  BriefcaseBusiness,
  ChevronRight,
  Database,
  FileSearch,
  FileText,
  Gauge,
  LockKeyhole,
  MessagesSquare,
  ShieldCheck,
  Sparkles,
  Trophy,
} from 'lucide-react';
import { apiFetch, getStoredToken } from '@/lib/api';

type RemindersResponse = {
  reminders: Array<{ id: string; severity: string }>;
};

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { href: '/runway', label: 'Runway', icon: Gauge },
  { href: '/resume', label: 'Resume', icon: FileText },
  { href: '/jobs', label: 'JD Match', icon: FileSearch },
  { href: '/applications', label: 'Applications', icon: BriefcaseBusiness },
  { href: '/proof', label: 'Proof', icon: Trophy },
  { href: '/interview', label: 'Interview', icon: MessagesSquare },
  { href: '/campaigns', label: 'Campaigns', icon: Bot },
  { href: '/settings/ai-providers', label: 'AI', icon: ShieldCheck },
  { href: '/settings/privacy', label: 'Privacy', icon: LockKeyhole },
];

function isActivePath(pathname: string, href: string) {
  if (href === '/dashboard') return pathname === href || pathname === '/';
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [token] = useState(() => getStoredToken());
  const remindersQuery = useQuery({
    queryKey: ['global-reminders'],
    queryFn: () => apiFetch<RemindersResponse>('/api/v1/reminders/'),
    enabled: Boolean(token),
  });
  const reminderCount = remindersQuery.data?.reminders?.length || 0;

  return (
    <div className="min-h-screen">
      <nav className="sticky top-0 z-50 border-b border-white/10 bg-neutral-950/85 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 sm:px-6 xl:min-h-16 xl:flex-row xl:items-center xl:justify-between">
          <Link href="/dashboard" className="group flex min-w-fit items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-emerald-400/25 bg-emerald-400/10 text-emerald-200 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
              <Sparkles className="h-4 w-4" aria-hidden="true" />
            </span>
            <span>
              <span className="block text-lg font-semibold tracking-tight text-white">ReboundIQ</span>
              <span className="block text-[11px] font-medium uppercase tracking-[0.18em] text-emerald-300/80">
                Local career OS
              </span>
            </span>
          </Link>

          <div className="-mx-4 flex gap-1 overflow-x-auto px-4 pb-1 xl:mx-0 xl:flex-wrap xl:justify-center xl:overflow-visible xl:px-0 xl:pb-0">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = isActivePath(pathname, item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? 'page' : undefined}
                  className={`nav-link ${active ? 'nav-link-active' : ''}`}
                >
                  <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>

          <div className="hidden min-w-fit items-center gap-2 text-xs text-zinc-400 xl:flex">
            <span className="status-dot status-dot-safe" />
            <span>Ollama local</span>
            <ChevronRight className="h-3.5 w-3.5 text-zinc-600" aria-hidden="true" />
            <span>Manual actions</span>
            {token && (
              <>
                <ChevronRight className="h-3.5 w-3.5 text-zinc-600" aria-hidden="true" />
                <Link href="/dashboard" className={reminderCount ? 'text-amber-200 underline' : 'text-zinc-500'}>
                  {reminderCount} reminders
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      <div className="border-b border-white/5 bg-neutral-900/45">
        <div className="mx-auto grid max-w-7xl grid-cols-1 gap-2 px-4 py-3 text-xs sm:grid-cols-3 sm:px-6">
          <div className="trust-chip">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-300" aria-hidden="true" />
            <span>External AI off by default</span>
          </div>
          <div className="trust-chip">
            <Database className="h-3.5 w-3.5 text-cyan-300" aria-hidden="true" />
            <span>User-isolated records</span>
          </div>
          <div className="trust-chip">
            <LockKeyhole className="h-3.5 w-3.5 text-amber-300" aria-hidden="true" />
            <span>Human approval before use</span>
          </div>
        </div>
      </div>

      <main className="mx-auto w-full max-w-7xl px-4 py-7 sm:px-6 lg:py-9">{children}</main>

      <footer className="border-t border-white/5 px-4 py-5 text-center text-[11px] leading-relaxed text-zinc-500">
        Planning guidance only. Not legal, financial, immigration, tax, or medical advice. Local AI default. Data stays yours.
      </footer>
    </div>
  );
}
