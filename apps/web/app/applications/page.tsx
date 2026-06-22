'use client';

import React, { useEffect, useMemo, useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  CalendarClock,
  CheckCircle2,
  CirclePlus,
  Columns3,
  FileText,
  List,
  RotateCcw,
  Search,
  ShieldCheck,
  Target,
} from 'lucide-react';
import { EmptyState, MetricCard, PageHeader, ProgressBar, SectionHeader } from '@/components/product-ui';

const STAGES = [
  'Saved',
  'Applied',
  'Recruiter',
  'Tech',
  'System Design',
  'Manager',
  'Final',
  'Offer',
  'Rejected',
  'Withdrawn',
] as const;

type Stage = (typeof STAGES)[number];
type SponsorshipSignal = 'Unknown' | 'Supports sponsorship' | 'Needs review';

type Application = {
  id: string;
  company: string;
  role: string;
  stage: Stage;
  match: number;
  priority: 'High' | 'Medium' | 'Low';
  lastTouch: string;
  followUpDue: string;
  resumeVersion: string;
  jdSnapshot: string;
  nextAction: string;
  sponsorshipSignal: SponsorshipSignal;
  notes: string;
};

const STORAGE_KEY = 'reboundiq.applications.v1';

const DEFAULT_APPS: Application[] = [
  {
    id: 'app-1',
    company: 'Northstar Robotics',
    role: 'Senior AI Platform Engineer',
    stage: 'Tech',
    match: 82,
    priority: 'High',
    lastTouch: '2026-06-15',
    followUpDue: '2026-06-20',
    resumeVersion: 'AI Platform v2',
    jdSnapshot: 'RAG, Python, distributed systems, observability, Kubernetes',
    nextAction: 'Prepare system design examples tied to actual platform work.',
    sponsorshipSignal: 'Needs review',
    notes: 'Recruiter asked for architecture depth and recent LLM platform examples.',
  },
  {
    id: 'app-2',
    company: 'FinOps Cloud',
    role: 'Backend AI Engineer',
    stage: 'Applied',
    match: 74,
    priority: 'Medium',
    lastTouch: '2026-06-12',
    followUpDue: '2026-06-19',
    resumeVersion: 'Backend AI v1',
    jdSnapshot: 'FastAPI, Postgres, evals, model gateway, data privacy',
    nextAction: 'Send a short manual follow-up after seven business days.',
    sponsorshipSignal: 'Unknown',
    notes: 'JD is strong on compliance and gateway experience.',
  },
  {
    id: 'app-3',
    company: 'Signal Works',
    role: 'Staff Software Engineer, AI Tools',
    stage: 'Saved',
    match: 68,
    priority: 'Low',
    lastTouch: '2026-06-18',
    followUpDue: '2026-06-24',
    resumeVersion: 'Staff Backend draft',
    jdSnapshot: 'TypeScript, developer tools, LLM workflows, security reviews',
    nextAction: 'Tailor resume before applying.',
    sponsorshipSignal: 'Supports sponsorship',
    notes: 'Needs proof asset showing productized tooling, not only prototypes.',
  },
  {
    id: 'app-4',
    company: 'Atlas Health Data',
    role: 'ML Infrastructure Lead',
    stage: 'Manager',
    match: 79,
    priority: 'High',
    lastTouch: '2026-06-17',
    followUpDue: '2026-06-21',
    resumeVersion: 'Infra Lead v1',
    jdSnapshot: 'MLOps, privacy, data pipelines, platform leadership',
    nextAction: 'Draft truthful leadership stories with citations to project work.',
    sponsorshipSignal: 'Needs review',
    notes: 'Hiring manager wants examples of tradeoff decisions.',
  },
];

const emptyDraft = {
  company: '',
  role: '',
  match: 65,
  priority: 'Medium' as Application['priority'],
  resumeVersion: 'Untitled resume version',
  jdSnapshot: '',
  nextAction: 'Review JD match output and decide whether to apply.',
  sponsorshipSignal: 'Unknown' as SponsorshipSignal,
  notes: '',
};

function daysUntil(date: string) {
  const today = new Date();
  const target = new Date(`${date}T12:00:00`);
  return Math.ceil((target.getTime() - today.getTime()) / 86_400_000);
}

function toIsoDate(date: Date) {
  return date.toISOString().slice(0, 10);
}

function addDays(days: number) {
  const next = new Date();
  next.setDate(next.getDate() + days);
  return toIsoDate(next);
}

function formatDueLabel(date: string) {
  const days = daysUntil(date);
  if (days < 0) return `${Math.abs(days)}d overdue`;
  if (days === 0) return 'due today';
  return `in ${days}d`;
}

function clampMatch(value: number) {
  return Math.max(0, Math.min(100, Math.round(value || 0)));
}

function parseStoredApps(raw: string | null) {
  if (!raw) return DEFAULT_APPS;

  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return DEFAULT_APPS;

    return parsed.filter((item): item is Application => {
      return (
        typeof item?.id === 'string' &&
        typeof item.company === 'string' &&
        typeof item.role === 'string' &&
        STAGES.includes(item.stage)
      );
    });
  } catch {
    return DEFAULT_APPS;
  }
}

export default function Applications() {
  const [applications, setApplications] = useState<Application[]>(DEFAULT_APPS);
  const [query, setQuery] = useState('');
  const [stageFilter, setStageFilter] = useState<'All' | Stage>('All');
  const [draft, setDraft] = useState(emptyDraft);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setApplications(parseStoredApps(window.localStorage.getItem(STORAGE_KEY)));
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (!isHydrated) return;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(applications));
  }, [applications, isHydrated]);

  const filteredApplications = useMemo(() => {
    const q = query.trim().toLowerCase();
    return applications.filter((app) => {
      const matchesQuery =
        !q ||
        [app.company, app.role, app.jdSnapshot, app.resumeVersion, app.notes]
          .join(' ')
          .toLowerCase()
          .includes(q);
      const matchesStage = stageFilter === 'All' || app.stage === stageFilter;
      return matchesQuery && matchesStage;
    });
  }, [applications, query, stageFilter]);

  const metrics = useMemo(() => {
    const active = applications.filter((app) => !['Rejected', 'Withdrawn', 'Offer'].includes(app.stage));
    const due = applications.filter((app) => daysUntil(app.followUpDue) <= 1 && !['Rejected', 'Withdrawn'].includes(app.stage));
    const avgMatch = applications.length
      ? Math.round(applications.reduce((sum, app) => sum + app.match, 0) / applications.length)
      : 0;

    return {
      active: active.length,
      due: due.length,
      avgMatch,
      interviews: applications.filter((app) => ['Tech', 'System Design', 'Manager', 'Final'].includes(app.stage)).length,
    };
  }, [applications]);

  function addApplication() {
    if (!draft.company.trim() || !draft.role.trim()) return;

    const nextApplication: Application = {
      ...draft,
      id: `app-${Date.now()}`,
      company: draft.company.trim(),
      role: draft.role.trim(),
      match: clampMatch(draft.match),
      stage: 'Saved',
      lastTouch: toIsoDate(new Date()),
      followUpDue: addDays(7),
    };

    setApplications((current) => [nextApplication, ...current]);
    setDraft(emptyDraft);
  }

  function moveApplication(id: string, direction: -1 | 1) {
    setApplications((current) =>
      current.map((app) => {
        if (app.id !== id) return app;
        const currentIndex = STAGES.indexOf(app.stage);
        const nextIndex = Math.max(0, Math.min(STAGES.length - 1, currentIndex + direction));
        return {
          ...app,
          stage: STAGES[nextIndex],
          lastTouch: toIsoDate(new Date()),
        };
      }),
    );
  }

  function resetDemo() {
    setApplications(DEFAULT_APPS);
    setQuery('');
    setStageFilter('All');
  }

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Application tracker"
        title="Manual pipeline with useful pressure"
        description="Track target roles, grounded snapshots, follow-up timing, and interview movement without auto-apply behavior."
        actions={
          <>
          <span className="pill border-emerald-900 bg-emerald-950 text-emerald-300">
            <ShieldCheck className="h-3.5 w-3.5" /> Manual send only
          </span>
          <span className="pill border-zinc-800 bg-zinc-900 text-zinc-300">
            <FileText className="h-3.5 w-3.5" /> JD snapshots local
          </span>
          </>
        }
      />

      <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <MetricCard label="Active" value={metrics.active} detail="roles still in play" icon={Columns3} />
        <MetricCard label="Follow-ups" value={metrics.due} detail="due today or tomorrow" icon={CalendarClock} tone="text-amber-300" />
        <MetricCard label="Average match" value={`${metrics.avgMatch}%`} detail="across tracked roles" icon={Target} tone="text-emerald-300" />
        <MetricCard label="Interview loops" value={metrics.interviews} detail="technical or manager stages" icon={List} tone="text-cyan-300" />
      </section>

      <section className="card-subtle">
        <div className="grid grid-cols-1 gap-4 text-sm md:grid-cols-[0.8fr_1.2fr] md:items-center">
          <div>
            <div className="muted-label">Pipeline health</div>
            <p className="mt-2 text-zinc-300">{metrics.active} active roles with {metrics.interviews} interview-stage conversations.</p>
          </div>
          <ProgressBar value={applications.length ? (metrics.interviews / applications.length) * 100 : 0} tone="bg-cyan-300" label="interview-stage share" />
        </div>
      </section>

      <section className="card">
        <SectionHeader title="Add target role" description="Keep each application tied to a resume version and JD snapshot." />
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end">
          <label className="flex-1 text-sm">
            <span className="mb-2 block text-zinc-400">Company</span>
            <input
              className="input"
              value={draft.company}
              onChange={(event) => setDraft((current) => ({ ...current, company: event.target.value }))}
              placeholder="Example: Northstar Robotics"
            />
          </label>
          <label className="flex-1 text-sm">
            <span className="mb-2 block text-zinc-400">Role</span>
            <input
              className="input"
              value={draft.role}
              onChange={(event) => setDraft((current) => ({ ...current, role: event.target.value }))}
              placeholder="Example: Senior AI Platform Engineer"
            />
          </label>
          <label className="w-full text-sm xl:w-32">
            <span className="mb-2 block text-zinc-400">Match</span>
            <input
              className="input"
              type="number"
              min={0}
              max={100}
              value={draft.match}
              onChange={(event) => setDraft((current) => ({ ...current, match: Number(event.target.value) }))}
            />
          </label>
          <label className="w-full text-sm xl:w-44">
            <span className="mb-2 block text-zinc-400">Priority</span>
            <select
              className="input"
              value={draft.priority}
              onChange={(event) =>
                setDraft((current) => ({ ...current, priority: event.target.value as Application['priority'] }))
              }
            >
              <option>High</option>
              <option>Medium</option>
              <option>Low</option>
            </select>
          </label>
          <button className="btn btn-primary" onClick={addApplication} disabled={!draft.company.trim() || !draft.role.trim()}>
            <CirclePlus className="h-4 w-4" /> Add
          </button>
        </div>
        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <label className="text-sm">
            <span className="mb-2 block text-zinc-400">Resume version</span>
            <input
              className="input"
              value={draft.resumeVersion}
              onChange={(event) => setDraft((current) => ({ ...current, resumeVersion: event.target.value }))}
            />
          </label>
          <label className="text-sm">
            <span className="mb-2 block text-zinc-400">Sponsorship signal</span>
            <select
              className="input"
              value={draft.sponsorshipSignal}
              onChange={(event) =>
                setDraft((current) => ({ ...current, sponsorshipSignal: event.target.value as SponsorshipSignal }))
              }
            >
              <option>Unknown</option>
              <option>Supports sponsorship</option>
              <option>Needs review</option>
            </select>
          </label>
        </div>
      </section>

      <section className="flex flex-col gap-3 md:flex-row">
        <label className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-zinc-500" aria-hidden="true" />
          <input
            className="input pl-9"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search company, role, JD snapshot, resume version"
          />
        </label>
        <select
          className="input md:w-56"
          value={stageFilter}
          onChange={(event) => setStageFilter(event.target.value as 'All' | Stage)}
        >
          <option>All</option>
          {STAGES.map((stage) => (
            <option key={stage}>{stage}</option>
          ))}
        </select>
        <button className="btn btn-secondary" onClick={resetDemo}>
          <RotateCcw className="h-4 w-4" /> Reset demo
        </button>
      </section>

      <section className="card lg:hidden">
        <SectionHeader title="Compact list" description="Mobile-friendly view of the filtered pipeline." />
        {filteredApplications.length ? (
          <div className="space-y-3">
            {filteredApplications.map((app) => {
              const dueDays = daysUntil(app.followUpDue);
              const dueClass = dueDays <= 0 ? 'text-red-300' : dueDays <= 2 ? 'text-amber-300' : 'text-zinc-400';
              return (
                <article key={app.id} className="rounded-lg border border-white/10 bg-black/20 p-4 text-sm">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h2 className="font-semibold leading-snug text-white">{app.company}</h2>
                      <p className="mt-1 text-xs text-zinc-400">{app.role}</p>
                    </div>
                    <span className="pill border-white/10 bg-white/[0.04] text-zinc-300">{app.stage}</span>
                  </div>
                  <div className="mt-4">
                    <ProgressBar value={app.match} tone="bg-emerald-300" label={`${app.match}% match`} />
                  </div>
                  <div className="mt-4 grid grid-cols-1 gap-2 text-xs text-zinc-400 sm:grid-cols-2">
                    <div className="flex items-center gap-1.5">
                      <CalendarClock className={`h-3.5 w-3.5 ${dueClass}`} />
                      <span className={dueClass}>{formatDueLabel(app.followUpDue)}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Target className="h-3.5 w-3.5 text-cyan-300" />
                      <span>{app.priority} priority</span>
                    </div>
                  </div>
                  <p className="mt-3 text-xs leading-relaxed text-zinc-300">{app.nextAction}</p>
                  <div className="mt-4 flex items-center justify-between gap-3">
                    <button
                      className="btn btn-secondary px-2 py-1"
                      onClick={() => moveApplication(app.id, -1)}
                      disabled={STAGES.indexOf(app.stage) === 0}
                      aria-label={`Move ${app.company} backward`}
                    >
                      <ArrowLeft className="h-3.5 w-3.5" />
                    </button>
                    <span className="text-[10px] text-zinc-500">{app.sponsorshipSignal}</span>
                    <button
                      className="btn btn-secondary px-2 py-1"
                      onClick={() => moveApplication(app.id, 1)}
                      disabled={STAGES.indexOf(app.stage) === STAGES.length - 1}
                      aria-label={`Move ${app.company} forward`}
                    >
                      <ArrowRight className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <EmptyState icon={Search} title="No matching applications" description="Adjust the search or stage filter to bring roles back into view." />
        )}
      </section>

      <section className="hidden overflow-x-auto pb-3 lg:block scroll-panel">
        <SectionHeader title="Kanban board" description="Large-screen pipeline view with explicit stage movement controls." />
        <div className="grid min-w-[1480px] grid-cols-10 gap-3">
          {STAGES.map((stage) => {
            const stageApps = filteredApplications.filter((app) => app.stage === stage);
            return (
              <div key={stage} className="rounded-lg border border-zinc-800 bg-zinc-950/70 p-3">
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-sm font-medium text-white">{stage}</h2>
                  <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-xs text-zinc-300">{stageApps.length}</span>
                </div>
                <div className="space-y-3">
                  {stageApps.map((app) => {
                    const dueDays = daysUntil(app.followUpDue);
                    const dueClass = dueDays <= 0 ? 'text-red-300' : dueDays <= 2 ? 'text-amber-300' : 'text-zinc-400';
                    return (
                      <article key={app.id} className="rounded-lg border border-zinc-800 bg-zinc-900 p-3 text-sm">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <h3 className="font-medium leading-snug text-white">{app.company}</h3>
                            <p className="mt-1 text-xs text-zinc-400">{app.role}</p>
                          </div>
                          <span className="rounded bg-zinc-950 px-2 py-1 text-xs text-emerald-300">{app.match}%</span>
                        </div>
                        <div className="mt-3 h-1.5 rounded bg-zinc-800">
                          <div className="h-1.5 rounded bg-emerald-500" style={{ width: `${app.match}%` }} />
                        </div>
                        <div className="mt-3 space-y-2 text-xs text-zinc-400">
                          <div className="flex items-center gap-1.5">
                            <CalendarClock className={`h-3.5 w-3.5 ${dueClass}`} />
                            <span className={dueClass}>{formatDueLabel(app.followUpDue)}</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <Target className="h-3.5 w-3.5 text-cyan-300" />
                            <span>{app.priority} priority</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-300" />
                            <span>{app.resumeVersion}</span>
                          </div>
                        </div>
                        <p className="mt-3 text-xs leading-relaxed text-zinc-300">{app.nextAction}</p>
                        <div className="mt-3 flex items-center justify-between">
                          <button
                            className="btn btn-secondary px-2 py-1"
                            onClick={() => moveApplication(app.id, -1)}
                            disabled={STAGES.indexOf(app.stage) === 0}
                            aria-label={`Move ${app.company} backward`}
                          >
                            <ArrowLeft className="h-3.5 w-3.5" />
                          </button>
                          <span className="text-[10px] text-zinc-500">{app.sponsorshipSignal}</span>
                          <button
                            className="btn btn-secondary px-2 py-1"
                            onClick={() => moveApplication(app.id, 1)}
                            disabled={STAGES.indexOf(app.stage) === STAGES.length - 1}
                            aria-label={`Move ${app.company} forward`}
                          >
                            <ArrowRight className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </article>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {filteredApplications.slice(0, 2).map((app) => (
          <article key={app.id} className="card">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="section-title">{app.company} scorecard</h2>
                <p className="mt-1 text-xs text-zinc-500">{app.role}</p>
              </div>
              <span className="pill border-zinc-800 bg-zinc-950 text-zinc-300">{app.stage}</span>
            </div>
            <dl className="mt-4 grid grid-cols-1 gap-3 text-sm md:grid-cols-2">
              <div>
                <dt className="text-xs text-zinc-500">JD snapshot</dt>
                <dd className="mt-1 text-zinc-300">{app.jdSnapshot}</dd>
              </div>
              <div>
                <dt className="text-xs text-zinc-500">Notes</dt>
                <dd className="mt-1 text-zinc-300">{app.notes}</dd>
              </div>
            </dl>
            <div className="disclaimer mt-4">
              Planning guidance only. Review sponsorship, compensation, legal, and immigration questions with qualified professionals.
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}
