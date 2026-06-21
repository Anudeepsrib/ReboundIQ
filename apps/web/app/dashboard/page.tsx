'use client';

import React from 'react';
import Link from 'next/link';
import {
  Bot,
  BriefcaseBusiness,
  CalendarCheck2,
  FileSearch,
  FileText,
  Gauge,
  MessagesSquare,
  ShieldCheck,
  Trophy,
} from 'lucide-react';

export default function Dashboard() {
  const workflows = [
    {
      href: '/runway',
      label: 'Model runway',
      detail: '82d moderate signal',
      icon: Gauge,
      accent: 'text-amber-300',
    },
    {
      href: '/applications',
      label: 'Track applications',
      detail: '4 active, 2 follow-ups',
      icon: BriefcaseBusiness,
      accent: 'text-cyan-300',
    },
    {
      href: '/proof',
      label: 'Build proof assets',
      detail: 'Evidence-first drafts',
      icon: Trophy,
      accent: 'text-emerald-300',
    },
    {
      href: '/interview',
      label: 'Practice interviews',
      detail: 'STAR and citation checks',
      icon: MessagesSquare,
      accent: 'text-violet-300',
    },
  ];

  return (
    <div className="space-y-8">
      <div className="mb-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">Layoff Recovery Dashboard</h1>
            <p className="text-zinc-400 mt-1">Demo user • Local AI (Ollama) • External disabled • All data private to you</p>
          </div>
          <div className="pill border-emerald-900 bg-emerald-950 text-emerald-300">
            <ShieldCheck className="h-3.5 w-3.5" /> Local-first mode
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="card">
          <div className="text-sm text-zinc-400">Layoff-to-Offer Progress</div>
          <div className="mt-3 h-2 bg-zinc-800 rounded"><div className="h-2 w-[42%] bg-emerald-500 rounded" /></div>
          <div className="mt-2 text-xs">Resume 78% • Applications 3/12 • Interview ready 35%</div>
        </div>
        <div className="card">
          <div className="text-sm text-zinc-400">Risk Signals</div>
          <ul className="mt-2 text-sm space-y-1">
            <li className="text-emerald-400">Runway: moderate (82d)</li>
            <li className="text-amber-400">Resume: 1 tailored version ready</li>
            <li className="text-red-400">Portfolio: 0 proof assets</li>
            <li>Visa sensitivity: H-1B (planning only)</li>
          </ul>
        </div>
        <div className="card">
          <div className="text-sm text-zinc-400">AI Provider</div>
          <div className="mt-2 text-lg font-medium">Ollama • local model selectable</div>
          <div className="text-emerald-400 text-xs mt-1">External AI: DISABLED (no consent)</div>
          <Link href="/settings/ai-providers" className="text-xs underline mt-2 inline-block">Configure providers</Link>
        </div>
      </div>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
        {workflows.map((workflow) => {
          const Icon = workflow.icon;
          return (
            <Link key={workflow.href} href={workflow.href} className="card block transition-colors hover:border-zinc-700">
              <div className="flex items-center justify-between gap-3">
                <Icon className={`h-5 w-5 ${workflow.accent}`} aria-hidden="true" />
                <span className="text-xs text-zinc-500">{workflow.detail}</span>
              </div>
              <div className="mt-4 font-medium text-white">{workflow.label}</div>
            </Link>
          );
        })}
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card">
          <h3 className="font-medium mb-3">Quick Actions</h3>
          <div className="flex flex-wrap gap-2">
            <Link href="/resume" className="btn btn-primary">
              <FileText className="h-4 w-4" /> Resume
            </Link>
            <Link href="/jobs" className="btn btn-secondary">
              <FileSearch className="h-4 w-4" /> JD Match
            </Link>
            <Link href="/campaigns" className="btn btn-secondary">
              <Bot className="h-4 w-4" /> Campaign
            </Link>
          </div>
          <div className="disclaimer mt-4">All generated content is editable. Source data and citations shown. Never overwrite originals.</div>
        </div>

        <div className="card">
          <h3 className="font-medium mb-3">This Week&apos;s Plan</h3>
          <ul className="text-sm space-y-2">
            <li className="flex gap-2"><CalendarCheck2 className="mt-0.5 h-4 w-4 text-emerald-300" /> Update resume for AI Engineer role.</li>
            <li className="flex gap-2"><CalendarCheck2 className="mt-0.5 h-4 w-4 text-emerald-300" /> Create 2 proof assets from verified project evidence.</li>
            <li className="flex gap-2"><CalendarCheck2 className="mt-0.5 h-4 w-4 text-emerald-300" /> Move 3 applications into the tracker with JD snapshots.</li>
            <li className="flex gap-2"><CalendarCheck2 className="mt-0.5 h-4 w-4 text-emerald-300" /> Complete 1 interview practice loop.</li>
          </ul>
          <div className="text-[10px] text-amber-400 mt-3">This is planning guidance, not advice. Adjust to your real constraints.</div>
        </div>
      </div>

      <div className="mt-8 text-xs text-zinc-500">
        ReboundIQ v0.1 vertical slice • See design in .design/ for full 23-PR plan • Local-first, consent-first, grounded, no fabrication.
      </div>
    </div>
  );
}
