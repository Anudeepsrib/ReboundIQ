'use client';

import Link from 'next/link';
import {
  ArrowRight,
  Bot,
  BriefcaseBusiness,
  CalendarCheck2,
  CheckCircle2,
  FileSearch,
  FileText,
  Gauge,
  LockKeyhole,
  MessagesSquare,
  ShieldCheck,
  Sparkles,
  Trophy,
} from 'lucide-react';

const metrics = [
  { label: 'Runway', value: '82d', detail: 'moderate pressure', tone: 'text-amber-300' },
  { label: 'Active apps', value: '4', detail: '2 follow-ups due', tone: 'text-cyan-300' },
  { label: 'Resume readiness', value: '78%', detail: '1 tailored version', tone: 'text-emerald-300' },
  { label: 'Interview readiness', value: '35%', detail: 'practice loop open', tone: 'text-violet-300' },
];

const workflows = [
  {
    href: '/runway',
    label: 'Runway planner',
    detail: 'Pressure, burn, and weekly risk signals',
    icon: Gauge,
    accent: 'text-amber-300',
  },
  {
    href: '/applications',
    label: 'Application tracker',
    detail: 'Manual pipeline with local JD snapshots',
    icon: BriefcaseBusiness,
    accent: 'text-cyan-300',
  },
  {
    href: '/proof',
    label: 'Proof builder',
    detail: 'STAR stories and assets from cited evidence',
    icon: Trophy,
    accent: 'text-emerald-300',
  },
  {
    href: '/interview',
    label: 'Interview prep',
    detail: 'Practice prompts, score history, boundaries',
    icon: MessagesSquare,
    accent: 'text-violet-300',
  },
];

const weeklyPlan = [
  'Tailor the AI Engineer resume version and preserve the original upload.',
  'Create two proof assets from verified project evidence.',
  'Move three target roles into the tracker with JD snapshots.',
  'Complete one system-design practice loop before outreach.',
];

const safetyPosture = [
  { label: 'Local model', value: 'Ollama selectable', icon: Bot, tone: 'text-cyan-300' },
  { label: 'External AI', value: 'Disabled until consent', icon: ShieldCheck, tone: 'text-emerald-300' },
  { label: 'Generated artifacts', value: 'Drafts only', icon: LockKeyhole, tone: 'text-amber-300' },
];

export default function Dashboard() {
  return (
    <div className="space-y-8">
      <header className="page-header">
        <div>
          <div className="eyebrow">Command center</div>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            Layoff-to-offer operating plan
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-400">
            Private recovery workflows for runway, resume evidence, applications, proof assets, and interview practice.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="pill border-emerald-400/20 bg-emerald-400/10 text-emerald-200">
            <ShieldCheck className="h-3.5 w-3.5" /> Local-first mode
          </span>
          <span className="pill border-cyan-400/20 bg-cyan-400/10 text-cyan-200">
            <Sparkles className="h-3.5 w-3.5" /> Evidence required
          </span>
        </div>
      </header>

      <section className="grid grid-cols-1 gap-5 xl:grid-cols-[1.45fr_0.55fr]">
        <div className="card overflow-hidden">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <div className="muted-label">Current recovery state</div>
              <div className="mt-3 text-5xl font-semibold tracking-tight text-white">42%</div>
              <p className="mt-2 text-sm text-zinc-400">Resume foundation is strong. Proof and interview loops are the next bottlenecks.</p>
            </div>
            <div className="grid min-w-[16rem] grid-cols-2 gap-3 text-sm">
              <div className="stat-card">
                <div className="text-zinc-500">Target cadence</div>
                <div className="mt-1 font-semibold text-white">12 roles / wk</div>
              </div>
              <div className="stat-card">
                <div className="text-zinc-500">Human gates</div>
                <div className="mt-1 font-semibold text-white">Required</div>
              </div>
            </div>
          </div>

          <div className="mt-6">
            <div className="progress-track">
              <div className="progress-fill w-[42%]" />
            </div>
            <div className="mt-3 grid grid-cols-2 gap-3 text-xs text-zinc-400 md:grid-cols-4">
              <span>Resume 78%</span>
              <span>Applications 25%</span>
              <span>Proof 0%</span>
              <span>Interview 35%</span>
            </div>
          </div>
        </div>

        <aside className="card">
          <div className="muted-label">Safety posture</div>
          <div className="mt-4 space-y-3">
            {safetyPosture.map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.label} className="flex items-start gap-3 rounded-lg border border-white/10 bg-black/20 p-3">
                  <Icon className={`mt-0.5 h-4 w-4 ${item.tone}`} aria-hidden="true" />
                  <div>
                    <div className="text-sm font-medium text-white">{item.label}</div>
                    <div className="mt-0.5 text-xs text-zinc-500">{item.value}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </aside>
      </section>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
        {metrics.map((metric) => (
          <article key={metric.label} className="card">
            <div className="text-sm text-zinc-400">{metric.label}</div>
            <div className={`metric mt-3 ${metric.tone}`}>{metric.value}</div>
            <div className="mt-2 text-xs text-zinc-500">{metric.detail}</div>
          </article>
        ))}
      </section>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
        {workflows.map((workflow) => {
          const Icon = workflow.icon;
          return (
            <Link key={workflow.href} href={workflow.href} className="card interactive-card group block">
              <div className="flex items-center justify-between gap-3">
                <Icon className={`h-5 w-5 ${workflow.accent}`} aria-hidden="true" />
                <ArrowRight className="h-4 w-4 text-zinc-600 transition-colors group-hover:text-white" aria-hidden="true" />
              </div>
              <div className="mt-4 font-semibold text-white">{workflow.label}</div>
              <p className="mt-2 min-h-10 text-sm leading-5 text-zinc-400">{workflow.detail}</p>
            </Link>
          );
        })}
      </section>

      <section className="grid grid-cols-1 gap-5 lg:grid-cols-[0.82fr_1.18fr]">
        <div className="card">
          <h2 className="section-title">Quick actions</h2>
          <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-3 lg:grid-cols-1">
            <Link href="/resume" className="btn btn-primary justify-between">
              <span className="inline-flex items-center gap-2">
                <FileText className="h-4 w-4" /> Resume
              </span>
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link href="/jobs" className="btn btn-secondary justify-between">
              <span className="inline-flex items-center gap-2">
                <FileSearch className="h-4 w-4" /> JD Match
              </span>
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link href="/campaigns" className="btn btn-secondary justify-between">
              <span className="inline-flex items-center gap-2">
                <Bot className="h-4 w-4" /> Campaign
              </span>
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="disclaimer mt-4">
            Generated content stays editable. Source data and citations remain visible before any use.
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between gap-3">
            <h2 className="section-title">This week&apos;s plan</h2>
            <span className="pill border-white/10 bg-white/[0.04] text-zinc-300">4 tasks</span>
          </div>
          <ol className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2">
            {weeklyPlan.map((item, index) => (
              <li key={item} className="flex gap-3 rounded-lg border border-white/10 bg-black/20 p-3 text-sm text-zinc-300">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-emerald-400/20 bg-emerald-400/10 text-xs font-semibold text-emerald-200">
                  {index + 1}
                </span>
                <span className="leading-5">{item}</span>
              </li>
            ))}
          </ol>
          <div className="mt-4 flex items-center gap-2 text-xs text-amber-300">
            <CalendarCheck2 className="h-4 w-4" /> Planning guidance only. Adjust to real constraints.
          </div>
        </div>
      </section>

      <section className="card-subtle flex flex-col gap-3 text-sm text-zinc-400 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-300" />
          <span>Deterministic services remain authoritative. Agents orchestrate and request approval.</span>
        </div>
        <Link href="/settings/privacy" className="text-emerald-200 underline">
          Review privacy controls
        </Link>
      </section>
    </div>
  );
}
