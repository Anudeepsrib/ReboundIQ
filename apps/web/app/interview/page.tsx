'use client';

import React, { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowRight, ClipboardList, History, LockKeyhole, MessageSquareText, Save, SlidersHorizontal, Trash2 } from 'lucide-react';
import { apiFetch, getStoredToken } from '@/lib/api';
import { EmptyState, MetricCard, PageHeader, ProgressBar, SectionHeader } from '@/components/product-ui';

const FOCUS_AREAS = ['behavioral', 'system_design', 'ai_rag', 'backend', 'leadership'] as const;
const CHECKS = ['STAR structure', 'Specific project evidence', 'Named tradeoff', 'No fabricated metric', 'Clear boundary'] as const;

type FocusArea = (typeof FOCUS_AREAS)[number];

type InterviewSession = {
  id: string;
  target_role: string;
  company?: string | null;
  interview_type: string;
  status: string;
  scheduled_at?: string | null;
  score?: number | null;
  focus_areas_json?: unknown[] | null;
  question_log_json?: Array<Record<string, unknown>> | null;
  feedback_json?: Record<string, unknown> | null;
  created_at: string;
};

const QUESTIONS: Record<FocusArea, string[]> = {
  behavioral: ['Tell me about a time you disagreed with a technical direction.', 'Describe a setback and how you rebuilt momentum.'],
  system_design: ['Design a private resume and JD analysis system with citations.', 'Design an application tracker with reminders and scorecards.'],
  ai_rag: ['How would you evaluate groundedness for a resume rewrite?', 'How would you route local and external model calls safely?'],
  backend: ['Walk through a FastAPI endpoint that enforces user isolation.', 'How would you design immutable resume uploads and versions?'],
  leadership: ['Tell me about optimizing safety over speed.', 'How would you lead a small team through this launch?'],
};

function label(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

export default function InterviewPrep() {
  const queryClient = useQueryClient();
  const [token] = useState(() => getStoredToken());
  const [focus, setFocus] = useState<FocusArea>('system_design');
  const [questionIndex, setQuestionIndex] = useState(0);
  const [targetRole, setTargetRole] = useState('Staff AI Engineer');
  const [company, setCompany] = useState('');
  const [notes, setNotes] = useState('');
  const [clarity, setClarity] = useState(3);
  const [depth, setDepth] = useState(3);
  const [checks, setChecks] = useState<Record<string, boolean>>({
    'STAR structure': true,
    'Specific project evidence': true,
    'Named tradeoff': false,
    'No fabricated metric': true,
    'Clear boundary': false,
  });

  const sessionsQuery = useQuery({
    queryKey: ['interview-sessions'],
    queryFn: () => apiFetch<InterviewSession[]>('/api/v1/interviews/sessions'),
    enabled: Boolean(token),
  });

  const currentQuestion = QUESTIONS[focus][questionIndex % QUESTIONS[focus].length];
  const checked = CHECKS.filter((check) => checks[check]).length;
  const score = Math.round((checked / CHECKS.length) * 60 + ((clarity + depth) / 10) * 40);

  const saveSession = useMutation({
    mutationFn: () =>
      apiFetch<InterviewSession>('/api/v1/interviews/sessions', {
        method: 'POST',
        body: JSON.stringify({
          target_role: targetRole,
          company: company || null,
          interview_type: focus === 'ai_rag' ? 'ai_rag' : focus === 'backend' ? 'mixed' : focus,
          status: 'completed',
          score,
          focus_areas_json: [focus],
          question_log_json: [{ prompt: currentQuestion, notes, checks, clarity, depth }],
          feedback_json: { score, checks_passed: checked, planning_guidance_only: true },
          metadata_json: { source: 'interview_practice' },
        }),
      }),
    onSuccess: () => {
      setNotes('');
      queryClient.invalidateQueries({ queryKey: ['interview-sessions'] });
    },
  });

  const deleteSession = useMutation({
    mutationFn: (id: string) => apiFetch(`/api/v1/interviews/sessions/${id}`, { method: 'DELETE' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['interview-sessions'] }),
  });

  const sessions = useMemo(() => sessionsQuery.data ?? [], [sessionsQuery.data]);
  const metrics = useMemo(() => {
    const avg = sessions.length ? Math.round(sessions.reduce((sum, session) => sum + Number(session.score || 0), 0) / sessions.length) : 0;
    return { avg, completed: sessions.filter((session) => session.status === 'completed').length };
  }, [sessions]);

  if (!token) {
    return (
      <div className="space-y-6">
        <PageHeader eyebrow="Interview prep" title="Login to save practice sessions" description="Interview attempts are persisted behind authenticated user isolation." actions={<span className="pill border-amber-400/20 bg-amber-400/10 text-amber-100"><LockKeyhole className="h-3.5 w-3.5" /> Login required</span>} />
        <a href="/login" className="btn btn-primary">Login / Create Demo User</a>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader eyebrow="Interview prep" title="Practice with evidence and persistence" description="Save practice sessions, scores, notes, focus areas, and campaign-promoted interview plans." />

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <MetricCard label="Focus" value={label(focus)} detail={`${QUESTIONS[focus].length} prompts`} icon={SlidersHorizontal} tone="text-cyan-300" />
        <MetricCard label="Current score" value={`${score}/100`} detail={`${checked}/${CHECKS.length} evidence checks`} icon={ClipboardList} tone={score >= 75 ? 'text-emerald-300' : 'text-amber-300'} />
        <MetricCard label="Saved sessions" value={sessions.length} detail={`${metrics.completed} completed`} icon={History} tone="text-violet-300" />
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="card">
          <SectionHeader title="Practice prompt" description="Answer from real evidence and save the session to your backend history." />
          <div className="mb-4 flex flex-wrap gap-2">
            {FOCUS_AREAS.map((area) => (
              <button key={area} className={`btn ${focus === area ? 'btn-primary' : 'btn-secondary'}`} onClick={() => { setFocus(area); setQuestionIndex(0); }}>
                {label(area)}
              </button>
            ))}
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
            <div className="text-xs uppercase text-cyan-300">{label(focus)}</div>
            <h2 className="mt-2 text-2xl font-semibold leading-snug text-white">{currentQuestion}</h2>
          </div>
          <div className="mt-5"><ProgressBar value={score} tone={score >= 75 ? 'bg-emerald-300' : 'bg-amber-300'} label="answer readiness" /></div>
          <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="text-sm"><span className="mb-2 block text-zinc-400">Target role</span><input className="input" value={targetRole} onChange={(event) => setTargetRole(event.target.value)} /></label>
            <label className="text-sm"><span className="mb-2 block text-zinc-400">Company</span><input className="input" value={company} onChange={(event) => setCompany(event.target.value)} placeholder="Optional" /></label>
          </div>
          <label className="mt-5 block text-sm"><span className="mb-2 block text-zinc-400">Answer notes</span><textarea className="input h-56" value={notes} onChange={(event) => setNotes(event.target.value)} /></label>
          <div className="mt-5 flex flex-wrap gap-2">
            <button className="btn btn-primary" onClick={() => saveSession.mutate()} disabled={saveSession.isPending || !notes.trim()}><Save className="h-4 w-4" /> Save session</button>
            <button className="btn btn-secondary" onClick={() => { setQuestionIndex((current) => current + 1); setNotes(''); }}><ArrowRight className="h-4 w-4" /> Next</button>
          </div>
        </div>

        <div className="space-y-4">
          <section className="card">
            <SectionHeader title="Evidence checklist" description="Specific and bounded answers score better." />
            <div className="space-y-3">
              {CHECKS.map((check) => (
                <label key={check} className="flex items-center justify-between gap-3 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm">
                  <span>{check}</span>
                  <input type="checkbox" checked={checks[check]} onChange={(event) => setChecks((current) => ({ ...current, [check]: event.target.checked }))} />
                </label>
              ))}
            </div>
          </section>
          <section className="card">
            <SectionHeader title="Self score" description="Local practice signal, not a hiring prediction." />
            <label className="block text-sm"><span className="mb-2 flex justify-between text-zinc-400">Clarity <span>{clarity}/5</span></span><input className="w-full" type="range" min={1} max={5} value={clarity} onChange={(event) => setClarity(Number(event.target.value))} /></label>
            <label className="mt-5 block text-sm"><span className="mb-2 flex justify-between text-zinc-400">Depth <span>{depth}/5</span></span><input className="w-full" type="range" min={1} max={5} value={depth} onChange={(event) => setDepth(Number(event.target.value))} /></label>
          </section>
        </div>
      </section>

      <section className="card">
        <SectionHeader title="Saved sessions" description="Backend-persisted sessions include practice attempts and approved campaign interview plans." action={<span className="text-xs text-zinc-500">Average {metrics.avg}/100</span>} />
        {sessions.length ? (
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
            {sessions.map((session) => (
              <article key={session.id} className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div><span className="text-xs text-cyan-300">{label(session.interview_type)}</span><h3 className="mt-2 font-medium text-white">{session.target_role}</h3></div>
                  <span className="text-sm font-semibold text-white">{Math.round(Number(session.score || 0))}</span>
                </div>
                <p className="mt-3 text-xs text-zinc-500">{session.company || 'No company'} | {new Date(session.created_at).toLocaleDateString()}</p>
                <button className="btn btn-secondary mt-4 px-3 py-1.5" onClick={() => deleteSession.mutate(session.id)}><Trash2 className="h-4 w-4" /> Delete</button>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState icon={MessageSquareText} title="No sessions saved yet" description="Write notes for a prompt and save the session to start your history." />
        )}
      </section>
    </div>
  );
}
