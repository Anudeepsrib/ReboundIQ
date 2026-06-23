'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AlertTriangle,
  ArrowRight,
  Bot,
  BriefcaseBusiness,
  CalendarCheck2,
  CheckCircle2,
  Clock3,
  Database,
  FileSearch,
  FileText,
  Gauge,
  LockKeyhole,
  MessagesSquare,
  RefreshCcw,
  ShieldCheck,
  Trophy,
} from 'lucide-react';
import { EmptyState, MetricCard, PageHeader, ProgressBar, SectionHeader } from '@/components/product-ui';
import { apiFetch, getStoredToken } from '@/lib/api';

type DashboardMetrics = {
  runway_months: number | null;
  runway_risk: string;
  active_applications: number;
  followups_due: number;
  average_fit_score: number;
  interview_stage_applications: number;
  resume_count: number;
  resume_version_count: number;
  proof_ready_count: number;
  proof_total_count: number;
  interview_completed_count: number;
  interview_average_score: number;
};

type Reminder = {
  id: string;
  title: string;
  detail: string;
  due_at?: string | null;
  source_type: string;
  source_id: string;
  severity: 'overdue' | 'due' | 'risk' | string;
  href: string;
};

type DashboardSummary = {
  readiness_score: number;
  readiness_note: string;
  metrics: DashboardMetrics;
  weekly_plan: string[];
  reminders: Reminder[];
  safety_posture: {
    deterministic_services: boolean;
    human_approval_required: boolean;
    external_actions_disabled: boolean;
  };
};

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

function runwayValue(months: number | null) {
  if (months === null || Number.isNaN(months)) return 'Set';
  return `${Math.round(months * 30.4375)}d`;
}

function riskTone(risk: string) {
  if (risk === 'critical' || risk === 'high') return 'text-red-300';
  if (risk === 'moderate') return 'text-amber-300';
  if (risk === 'stable') return 'text-emerald-300';
  return 'text-zinc-300';
}

function reminderTone(severity: string) {
  if (severity === 'overdue') return 'border-red-900 bg-red-950/40 text-red-200';
  if (severity === 'risk') return 'border-amber-900 bg-amber-950/40 text-amber-200';
  return 'border-cyan-900 bg-cyan-950/30 text-cyan-200';
}

function dueLabel(value?: string | null) {
  if (!value) return 'Review now';
  const due = new Date(value);
  if (Number.isNaN(due.getTime())) return 'Review now';
  const days = Math.ceil((due.getTime() - Date.now()) / 86_400_000);
  if (days < 0) return `${Math.abs(days)}d overdue`;
  if (days === 0) return 'due today';
  return `in ${days}d`;
}

export default function Dashboard() {
  const [token] = useState(() => getStoredToken());
  const summaryQuery = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => apiFetch<DashboardSummary>('/api/v1/dashboard/summary'),
    enabled: Boolean(token),
  });

  const summary = summaryQuery.data;
  const metrics = summary?.metrics;
  const recoveryScore = summary?.readiness_score ?? 0;
  const metricCards = useMemo(() => {
    if (!metrics) return [];
    return [
      {
        label: 'Runway',
        value: runwayValue(metrics.runway_months),
        detail:
          metrics.runway_months === null
            ? 'create a snapshot'
            : `${metrics.runway_months.toFixed(1)} months, ${metrics.runway_risk} risk`,
        tone: riskTone(metrics.runway_risk),
        icon: Gauge,
      },
      {
        label: 'Active apps',
        value: metrics.active_applications,
        detail: `${metrics.followups_due} follow-up${metrics.followups_due === 1 ? '' : 's'} due`,
        tone: 'text-cyan-300',
        icon: BriefcaseBusiness,
      },
      {
        label: 'Resume versions',
        value: metrics.resume_version_count,
        detail: `${metrics.resume_count} source resume${metrics.resume_count === 1 ? '' : 's'}`,
        tone: metrics.resume_version_count ? 'text-emerald-300' : 'text-amber-300',
        icon: FileText,
      },
      {
        label: 'Proof ready',
        value: `${metrics.proof_ready_count}/${metrics.proof_total_count}`,
        detail: 'approved or ready assets',
        tone: metrics.proof_ready_count ? 'text-emerald-300' : 'text-amber-300',
        icon: Trophy,
      },
    ];
  }, [metrics]);

  if (!token) {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Command center"
          title="Login to load your operating plan"
          description="Dashboard metrics are computed from user-isolated backend records. No demo progress is shown for unauthenticated sessions."
          actions={
            <span className="pill border-amber-400/20 bg-amber-400/10 text-amber-100">
              <LockKeyhole className="h-3.5 w-3.5" /> Login required
            </span>
          }
        />
        <Link href="/login" className="btn btn-primary">
          Login / Create Demo User
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Command center"
        title="Layoff-to-offer operating plan"
        description="Live recovery metrics, follow-ups, and planning signals from your authenticated backend workspace."
        actions={
          <>
            <span className="pill border-emerald-400/20 bg-emerald-400/10 text-emerald-200">
              <ShieldCheck className="h-3.5 w-3.5" /> Local-first mode
            </span>
            <button className="btn btn-secondary px-3 py-1.5" onClick={() => summaryQuery.refetch()} disabled={summaryQuery.isFetching}>
              <RefreshCcw className="h-4 w-4" /> Refresh
            </button>
          </>
        }
      />

      {summaryQuery.error && (
        <section className="rounded-lg border border-red-400/25 bg-red-500/10 p-4 text-sm text-red-100">
          Dashboard API unavailable: {summaryQuery.error instanceof Error ? summaryQuery.error.message : 'Unable to load summary'}
        </section>
      )}

      <section className="grid grid-cols-1 gap-5 xl:grid-cols-[1.45fr_0.55fr]">
        <div className="card overflow-hidden">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <div className="muted-label">Current recovery state</div>
              <div className="mt-3 text-5xl font-semibold tracking-tight text-white">
                {summaryQuery.isLoading ? '...' : `${recoveryScore}%`}
              </div>
              <p className="mt-2 text-sm text-zinc-400">
                {summary?.readiness_note || 'Computed from saved resumes, applications, proof assets, interviews, and runway.'}
              </p>
            </div>
            <div className="grid min-w-[16rem] grid-cols-2 gap-3 text-sm">
              <div className="stat-card">
                <div className="text-zinc-500">Interview loops</div>
                <div className="mt-1 font-semibold text-white">{metrics?.interview_stage_applications ?? 0}</div>
              </div>
              <div className="stat-card">
                <div className="text-zinc-500">Avg interview</div>
                <div className="mt-1 font-semibold text-white">{metrics?.interview_average_score ?? 0}/100</div>
              </div>
            </div>
          </div>

          <div className="mt-6">
            <ProgressBar value={recoveryScore} tone="bg-emerald-300" label="readiness" />
            <div className="mt-3 grid grid-cols-2 gap-3 text-xs text-zinc-400 md:grid-cols-4">
              <span>Fit {metrics?.average_fit_score ?? 0}%</span>
              <span>Apps {metrics?.active_applications ?? 0}</span>
              <span>Proof {metrics?.proof_ready_count ?? 0}</span>
              <span>Practice {metrics?.interview_completed_count ?? 0}</span>
            </div>
          </div>
        </div>

        <aside className="card">
          <div className="muted-label">Safety posture</div>
          <div className="mt-4 space-y-3">
            {[
              {
                label: 'Deterministic services',
                value: summary?.safety_posture.deterministic_services ? 'Authoritative' : 'Review needed',
                icon: Database,
                tone: 'text-cyan-300',
              },
              {
                label: 'Human gates',
                value: summary?.safety_posture.human_approval_required ? 'Required' : 'Review needed',
                icon: LockKeyhole,
                tone: 'text-amber-300',
              },
              {
                label: 'External actions',
                value: summary?.safety_posture.external_actions_disabled ? 'Disabled' : 'Review needed',
                icon: ShieldCheck,
                tone: 'text-emerald-300',
              },
            ].map((item) => {
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
        {metricCards.map((metric) => (
          <MetricCard key={metric.label} {...metric} />
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

      <section className="grid grid-cols-1 gap-5 lg:grid-cols-[0.78fr_1.22fr]">
        <div className="card">
          <SectionHeader
            title="Reminders"
            description="Backend-generated follow-ups, scheduled practice, and runway risk signals."
            action={<span className="pill border-white/10 bg-white/[0.04] text-zinc-300">{summary?.reminders.length ?? 0} open</span>}
          />
          <div className="space-y-3">
            {(summary?.reminders || []).map((reminder) => (
              <Link key={reminder.id} href={reminder.href} className="block rounded-lg border border-zinc-800 bg-zinc-950 p-3 transition-colors hover:border-zinc-700">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="font-medium text-white">{reminder.title}</div>
                    <p className="mt-1 text-xs leading-5 text-zinc-500">{reminder.detail}</p>
                  </div>
                  <span className={`pill shrink-0 ${reminderTone(reminder.severity)}`}>{dueLabel(reminder.due_at)}</span>
                </div>
              </Link>
            ))}
            {!summary?.reminders?.length && (
              <EmptyState icon={Clock3} title="No active reminders" description="Due follow-ups, scheduled practice, and runway risks will appear here." />
            )}
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between gap-3">
            <h2 className="section-title">This week&apos;s plan</h2>
            <span className="pill border-white/10 bg-white/[0.04] text-zinc-300">{summary?.weekly_plan.length ?? 0} tasks</span>
          </div>
          {summary?.weekly_plan.length ? (
            <ol className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2">
              {summary.weekly_plan.map((item, index) => (
                <li key={item} className="flex gap-3 rounded-lg border border-white/10 bg-black/20 p-3 text-sm text-zinc-300">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-emerald-400/20 bg-emerald-400/10 text-xs font-semibold text-emerald-200">
                    {index + 1}
                  </span>
                  <span className="leading-5">{item}</span>
                </li>
              ))}
            </ol>
          ) : (
            <EmptyState icon={CalendarCheck2} title="No weekly tasks yet" description="Add resume, runway, application, proof, or interview records to generate plan steps." />
          )}
          <div className="mt-4 flex items-center gap-2 text-xs text-amber-300">
            <CalendarCheck2 className="h-4 w-4" /> Planning guidance only. Adjust to real constraints.
          </div>
        </div>
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

        <div className="card-subtle flex flex-col gap-3 text-sm text-zinc-400 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-2">
            {summary?.safety_posture.deterministic_services ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-300" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-amber-300" />
            )}
            <span>Deterministic services remain authoritative. Agents orchestrate and request approval.</span>
          </div>
          <Link href="/settings/privacy" className="text-emerald-200 underline">
            Review privacy controls
          </Link>
        </div>
      </section>
    </div>
  );
}
