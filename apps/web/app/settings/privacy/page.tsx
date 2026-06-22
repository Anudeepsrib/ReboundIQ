'use client';

import { Archive, Database, FileDown, LockKeyhole, ShieldCheck, Trash2 } from 'lucide-react';

const controls = [
  {
    title: 'Export all data',
    detail: 'Resume records, applications, memories, vectors, audit rows, and generated artifacts.',
    icon: FileDown,
    tone: 'text-cyan-300',
  },
  {
    title: 'Hard delete account',
    detail: 'Cascade user-owned artifacts and vectors where appropriate. Originals remain governed by the deletion flow.',
    icon: Trash2,
    tone: 'text-red-300',
  },
  {
    title: 'External AI consent',
    detail: 'External providers stay disabled unless consent, redaction, and audit logging are active.',
    icon: ShieldCheck,
    tone: 'text-emerald-300',
  },
  {
    title: 'Sensitive memory categories',
    detail: 'Visa, finances, health, and other sensitive categories require explicit consent before memory use.',
    icon: LockKeyhole,
    tone: 'text-amber-300',
  },
];

const auditRows = [
  ['AI requests', 'ai_requests'],
  ['Agent tools', 'agent_tool_calls'],
  ['Memory events', 'memory_*'],
  ['User actions', 'action_audit_logs'],
];

export default function Privacy() {
  return (
    <div className="space-y-8">
      <header className="page-header">
        <div>
          <div className="eyebrow">Privacy controls</div>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">Data stays user-scoped</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-400">
            ReboundIQ defaults to local AI, user-isolated records, consent gates, and auditable generation paths.
          </p>
        </div>
        <span className="pill border-emerald-400/20 bg-emerald-400/10 text-emerald-200">
          <ShieldCheck className="h-3.5 w-3.5" /> Privacy-first
        </span>
      </header>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <div className="card">
          <div className="text-sm text-zinc-400">AI default</div>
          <div className="metric mt-3 text-emerald-300">Local</div>
          <div className="mt-2 text-xs text-zinc-500">Ollama provider path</div>
        </div>
        <div className="card">
          <div className="text-sm text-zinc-400">External calls</div>
          <div className="metric mt-3 text-amber-300">Opt-in</div>
          <div className="mt-2 text-xs text-zinc-500">Consent plus redaction</div>
        </div>
        <div className="card">
          <div className="text-sm text-zinc-400">Storage</div>
          <div className="metric mt-3 text-cyan-300">Scoped</div>
          <div className="mt-2 text-xs text-zinc-500">Authenticated user_id filters</div>
        </div>
        <div className="card">
          <div className="text-sm text-zinc-400">Actions</div>
          <div className="metric mt-3">Manual</div>
          <div className="mt-2 text-xs text-zinc-500">No auto-send behavior</div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-5 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="card">
          <h2 className="section-title">Controls</h2>
          <div className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2">
            {controls.map((control) => {
              const Icon = control.icon;
              return (
                <article key={control.title} className="rounded-lg border border-white/10 bg-black/20 p-4">
                  <Icon className={`h-5 w-5 ${control.tone}`} aria-hidden="true" />
                  <h3 className="mt-4 font-semibold text-white">{control.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-zinc-400">{control.detail}</p>
                </article>
              );
            })}
          </div>
        </div>

        <aside className="card">
          <div className="flex items-center gap-2">
            <Archive className="h-4 w-4 text-cyan-300" aria-hidden="true" />
            <h2 className="section-title">Audit surfaces</h2>
          </div>
          <div className="mt-5 space-y-3">
            {auditRows.map(([label, table]) => (
              <div key={table} className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-black/20 p-3 text-sm">
                <span className="text-zinc-300">{label}</span>
                <code className="rounded border border-white/10 bg-black/30 px-2 py-1 text-xs text-zinc-400">{table}</code>
              </div>
            ))}
          </div>
          <div className="disclaimer mt-5">
            See PRIVACY.md and SECURITY.md in the repo for the complete production posture.
          </div>
        </aside>
      </section>

      <section className="card-subtle flex items-start gap-3 text-sm leading-6 text-zinc-400">
        <Database className="mt-1 h-4 w-4 shrink-0 text-emerald-300" />
        <p>
          Export and delete flows are represented here as product controls in this demo slice. Backend implementations should preserve cascade safety,
          auditability, and user isolation.
        </p>
      </section>
    </div>
  );
}
