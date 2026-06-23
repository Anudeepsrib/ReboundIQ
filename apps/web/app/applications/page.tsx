'use client';

import React, { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, ArrowRight, CalendarClock, CirclePlus, Columns3, LockKeyhole, Search, Target, Trash2 } from 'lucide-react';
import { apiFetch, getStoredToken } from '@/lib/api';
import { EmptyState, MetricCard, PageHeader, ProgressBar, SectionHeader } from '@/components/product-ui';

const STAGES = ['saved', 'applied', 'recruiter', 'tech', 'system_design', 'manager', 'final', 'offer', 'rejected', 'withdrawn'] as const;
type Stage = (typeof STAGES)[number];

type Application = {
  id: string;
  company: string;
  role: string;
  status: Stage;
  source_url?: string | null;
  location?: string | null;
  salary_range?: string | null;
  resume_version_id?: string | null;
  jd_snapshot?: string | null;
  notes?: string | null;
  next_step?: string | null;
  next_step_at?: string | null;
  fit_score?: number | null;
  sponsorship_signal?: string | null;
  metadata_json?: Record<string, unknown> | null;
  created_at: string;
};

type ResumeVersion = {
  id: string;
  version_name: string;
  target_role?: string | null;
};

function label(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

function dateInput(days: number) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
}

function dueLabel(value?: string | null) {
  if (!value) return 'no date';
  const days = Math.ceil((new Date(`${value.slice(0, 10)}T12:00:00`).getTime() - Date.now()) / 86_400_000);
  if (days < 0) return `${Math.abs(days)}d overdue`;
  if (days === 0) return 'due today';
  return `in ${days}d`;
}

export default function Applications() {
  const queryClient = useQueryClient();
  const [token] = useState(() => getStoredToken());
  const [query, setQuery] = useState('');
  const [stageFilter, setStageFilter] = useState<'all' | Stage>('all');
  const [draft, setDraft] = useState({
    company: '',
    role: '',
    fit_score: 70,
    next_step: 'Review JD match and decide next action.',
    next_step_at: dateInput(7),
    sponsorship_signal: 'unknown',
    source_url: '',
    location: '',
    salary_range: '',
    resume_version_id: '',
    jd_snapshot: '',
    notes: '',
  });

  const applicationsQuery = useQuery({
    queryKey: ['applications'],
    queryFn: () => apiFetch<Application[]>('/api/v1/applications'),
    enabled: Boolean(token),
  });

  const versionsQuery = useQuery({
    queryKey: ['resume-versions'],
    queryFn: () => apiFetch<ResumeVersion[]>('/api/v1/resumes/versions'),
    enabled: Boolean(token),
  });

  const createApplication = useMutation({
    mutationFn: () =>
      apiFetch<Application>('/api/v1/applications', {
        method: 'POST',
        body: JSON.stringify({
          ...draft,
          company: draft.company.trim(),
          role: draft.role.trim(),
          status: 'saved',
          next_step_at: draft.next_step_at ? `${draft.next_step_at}T12:00:00Z` : null,
          source_url: draft.source_url.trim() || null,
          location: draft.location.trim() || null,
          salary_range: draft.salary_range.trim() || null,
          resume_version_id: draft.resume_version_id || null,
          metadata_json: { priority: Number(draft.fit_score) >= 80 ? 'high' : 'medium' },
        }),
      }),
    onSuccess: () => {
      setDraft({
        company: '',
        role: '',
        fit_score: 70,
        next_step: 'Review JD match and decide next action.',
        next_step_at: dateInput(7),
        sponsorship_signal: 'unknown',
        source_url: '',
        location: '',
        salary_range: '',
        resume_version_id: '',
        jd_snapshot: '',
        notes: '',
      });
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
  });

  const updateApplication = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<Application> }) =>
      apiFetch<Application>(`/api/v1/applications/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['applications'] }),
  });

  const deleteApplication = useMutation({
    mutationFn: (id: string) => apiFetch(`/api/v1/applications/${id}`, { method: 'DELETE' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['applications'] }),
  });

  const applications = useMemo(() => applicationsQuery.data ?? [], [applicationsQuery.data]);
  const versionNames = useMemo(() => {
    return new Map((versionsQuery.data || []).map((version) => [version.id, version.version_name]));
  }, [versionsQuery.data]);
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return applications.filter((app) => {
      const matchesStage = stageFilter === 'all' || app.status === stageFilter;
      const haystack = [app.company, app.role, app.jd_snapshot, app.notes, app.next_step].join(' ').toLowerCase();
      return matchesStage && (!q || haystack.includes(q));
    });
  }, [applications, query, stageFilter]);

  const metrics = useMemo(() => {
    const active = applications.filter((app) => !['offer', 'rejected', 'withdrawn'].includes(app.status)).length;
    const interviews = applications.filter((app) => ['tech', 'system_design', 'manager', 'final'].includes(app.status)).length;
    const due = applications.filter((app) => app.next_step_at && dueLabel(app.next_step_at).includes('due')).length;
    const avg = applications.length ? Math.round(applications.reduce((sum, app) => sum + Number(app.fit_score || 0), 0) / applications.length) : 0;
    return { active, interviews, due, avg };
  }, [applications]);

  function move(app: Application, direction: -1 | 1) {
    const index = STAGES.indexOf(app.status);
    const next = STAGES[Math.max(0, Math.min(STAGES.length - 1, index + direction))];
    updateApplication.mutate({ id: app.id, payload: { status: next, next_step_at: `${dateInput(3)}T12:00:00Z` } });
  }

  if (!token) {
    return (
      <div className="space-y-6">
        <PageHeader eyebrow="Application tracker" title="Login to manage your pipeline" description="Applications are persisted behind authenticated user isolation." actions={<span className="pill border-amber-400/20 bg-amber-400/10 text-amber-100"><LockKeyhole className="h-3.5 w-3.5" /> Login required</span>} />
        <a href="/login" className="btn btn-primary">Login / Create Demo User</a>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader eyebrow="Application tracker" title="Authenticated manual pipeline" description="Track roles, JD snapshots, next steps, sponsorship signals, and movement without auto-apply behavior." />

      <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <MetricCard label="Active" value={metrics.active} detail="roles still in play" icon={Columns3} />
        <MetricCard label="Follow-ups" value={metrics.due} detail="due or overdue" icon={CalendarClock} tone="text-amber-300" />
        <MetricCard label="Average fit" value={`${metrics.avg}%`} detail="across saved records" icon={Target} tone="text-emerald-300" />
        <MetricCard label="Interview loops" value={metrics.interviews} detail="tech through final" icon={Columns3} tone="text-cyan-300" />
      </section>

      <section className="card-subtle">
        <ProgressBar value={applications.length ? (metrics.interviews / applications.length) * 100 : 0} tone="bg-cyan-300" label="interview-stage share" />
      </section>

      <section className="card">
        <SectionHeader title="Add target role" description="Saved to the backend with user_id isolation and action audit." />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <label className="text-sm"><span className="mb-2 block text-zinc-400">Company</span><input className="input" value={draft.company} onChange={(event) => setDraft({ ...draft, company: event.target.value })} /></label>
          <label className="text-sm"><span className="mb-2 block text-zinc-400">Role</span><input className="input" value={draft.role} onChange={(event) => setDraft({ ...draft, role: event.target.value })} /></label>
          <label className="text-sm"><span className="mb-2 block text-zinc-400">Fit score</span><input className="input" type="number" min={0} max={100} value={draft.fit_score} onChange={(event) => setDraft({ ...draft, fit_score: Number(event.target.value) })} /></label>
          <label className="text-sm"><span className="mb-2 block text-zinc-400">Source URL</span><input className="input" value={draft.source_url} onChange={(event) => setDraft({ ...draft, source_url: event.target.value })} /></label>
          <label className="text-sm"><span className="mb-2 block text-zinc-400">Location</span><input className="input" value={draft.location} onChange={(event) => setDraft({ ...draft, location: event.target.value })} /></label>
          <label className="text-sm"><span className="mb-2 block text-zinc-400">Salary range</span><input className="input" value={draft.salary_range} onChange={(event) => setDraft({ ...draft, salary_range: event.target.value })} /></label>
          <label className="text-sm"><span className="mb-2 block text-zinc-400">Next step date</span><input className="input" type="date" value={draft.next_step_at} onChange={(event) => setDraft({ ...draft, next_step_at: event.target.value })} /></label>
          <label className="text-sm"><span className="mb-2 block text-zinc-400">Sponsorship signal</span><input className="input" value={draft.sponsorship_signal} onChange={(event) => setDraft({ ...draft, sponsorship_signal: event.target.value })} /></label>
          <label className="text-sm"><span className="mb-2 block text-zinc-400">Next step</span><input className="input" value={draft.next_step} onChange={(event) => setDraft({ ...draft, next_step: event.target.value })} /></label>
          <label className="text-sm lg:col-span-3">
            <span className="mb-2 block text-zinc-400">Resume version</span>
            <select className="input" value={draft.resume_version_id} onChange={(event) => setDraft({ ...draft, resume_version_id: event.target.value })}>
              <option value="">No tailored version linked</option>
              {(versionsQuery.data || []).map((version) => (
                <option key={version.id} value={version.id}>
                  {version.version_name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm lg:col-span-3"><span className="mb-2 block text-zinc-400">JD snapshot</span><textarea className="input h-24" value={draft.jd_snapshot} onChange={(event) => setDraft({ ...draft, jd_snapshot: event.target.value })} /></label>
          <label className="text-sm lg:col-span-3"><span className="mb-2 block text-zinc-400">Notes</span><textarea className="input h-20" value={draft.notes} onChange={(event) => setDraft({ ...draft, notes: event.target.value })} /></label>
        </div>
        <button className="btn btn-primary mt-5" onClick={() => createApplication.mutate()} disabled={createApplication.isPending || !draft.company.trim() || !draft.role.trim()}>
          <CirclePlus className="h-4 w-4" /> {createApplication.isPending ? 'Saving...' : 'Add application'}
        </button>
      </section>

      <section className="flex flex-col gap-3 md:flex-row">
        <label className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
          <input className="input pl-9" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search company, role, JD snapshot, notes" />
        </label>
        <select className="input md:w-56" value={stageFilter} onChange={(event) => setStageFilter(event.target.value as 'all' | Stage)}>
          <option value="all">All stages</option>
          {STAGES.map((stage) => <option key={stage} value={stage}>{label(stage)}</option>)}
        </select>
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {filtered.map((app) => (
          <article key={app.id} className="card">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="font-semibold text-white">{app.company}</h2>
                <p className="mt-1 text-sm text-zinc-400">{app.role}</p>
              </div>
              <span className="pill border-zinc-800 bg-zinc-950 text-zinc-300">{label(app.status)}</span>
            </div>
            <div className="mt-4"><ProgressBar value={Number(app.fit_score || 0)} tone="bg-emerald-300" label={`${Number(app.fit_score || 0)}% fit`} /></div>
            <dl className="mt-4 grid grid-cols-1 gap-3 text-sm md:grid-cols-2">
              <div><dt className="text-xs text-zinc-500">Next step</dt><dd className="mt-1 text-zinc-300">{app.next_step || 'Not set'}</dd></div>
              <div><dt className="text-xs text-zinc-500">Due</dt><dd className="mt-1 text-zinc-300">{dueLabel(app.next_step_at)}</dd></div>
              <div><dt className="text-xs text-zinc-500">Location</dt><dd className="mt-1 text-zinc-300">{app.location || 'Not captured'}</dd></div>
              <div><dt className="text-xs text-zinc-500">Salary</dt><dd className="mt-1 text-zinc-300">{app.salary_range || 'Not captured'}</dd></div>
              <div><dt className="text-xs text-zinc-500">Sponsorship</dt><dd className="mt-1 text-zinc-300">{app.sponsorship_signal || 'unknown'}</dd></div>
              <div><dt className="text-xs text-zinc-500">Resume version</dt><dd className="mt-1 text-zinc-300">{app.resume_version_id ? versionNames.get(app.resume_version_id) || app.resume_version_id : 'Not linked'}</dd></div>
              <div><dt className="text-xs text-zinc-500">Source</dt><dd className="mt-1 text-zinc-300">{app.source_url ? <a className="text-cyan-200 underline" href={app.source_url} target="_blank" rel="noreferrer">Open posting</a> : 'Not captured'}</dd></div>
              <div><dt className="text-xs text-zinc-500">JD snapshot</dt><dd className="mt-1 line-clamp-3 text-zinc-300">{app.jd_snapshot || 'Not captured'}</dd></div>
            </dl>
            <div className="mt-5 flex flex-wrap gap-2">
              <button className="btn btn-secondary px-3 py-1.5" onClick={() => move(app, -1)} disabled={app.status === 'saved'}><ArrowLeft className="h-4 w-4" /> Back</button>
              <button className="btn btn-secondary px-3 py-1.5" onClick={() => move(app, 1)} disabled={app.status === 'withdrawn'}><ArrowRight className="h-4 w-4" /> Forward</button>
              <button className="btn btn-secondary px-3 py-1.5" onClick={() => deleteApplication.mutate(app.id)}><Trash2 className="h-4 w-4" /> Delete</button>
            </div>
          </article>
        ))}
        {!filtered.length && <EmptyState icon={Search} title="No applications found" description="Add a target role or adjust the current filter." />}
      </section>
    </div>
  );
}
