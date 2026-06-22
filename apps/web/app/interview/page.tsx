'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { ArrowRight, CheckCircle2, ClipboardList, History, MessageSquareText, RotateCcw, Save, SlidersHorizontal } from 'lucide-react';
import { EmptyState, MetricCard, PageHeader, ProgressBar, SectionHeader } from '@/components/product-ui';

const FOCUS_AREAS = ['Behavioral', 'System Design', 'AI/RAG', 'Backend', 'Leadership'] as const;
const CHECKS = ['STAR structure', 'Specific project evidence', 'Named tradeoff', 'No fabricated metric', 'Clear boundary'] as const;

type FocusArea = (typeof FOCUS_AREAS)[number];
type CheckName = (typeof CHECKS)[number];

type Question = {
  id: string;
  focus: FocusArea;
  prompt: string;
  evidence: string;
  followUp: string;
};

type Attempt = {
  id: string;
  prompt: string;
  focus: FocusArea;
  score: number;
  savedAt: string;
  notes: string;
};

const STORAGE_KEY = 'reboundiq.interview-attempts.v1';

const QUESTIONS: Question[] = [
  {
    id: 'behavior-1',
    focus: 'Behavioral',
    prompt: 'Tell me about a time you disagreed with a technical direction and changed the outcome.',
    evidence: 'Decision record, design review, incident note, or shipped implementation.',
    followUp: 'What did you compromise on, and what would you do differently now?',
  },
  {
    id: 'behavior-2',
    focus: 'Behavioral',
    prompt: 'Describe a time you had to rebuild momentum after a setback.',
    evidence: 'Before/after state, stakeholder feedback, timeline, and concrete action taken.',
    followUp: 'How did you know the recovery plan was working?',
  },
  {
    id: 'system-1',
    focus: 'System Design',
    prompt: 'Design a private resume and JD analysis system with citations and audit logs.',
    evidence: 'Storage model, user isolation plan, RAG citation flow, audit/event schema.',
    followUp: 'Where do you enforce consent and redaction, and how do you test that path?',
  },
  {
    id: 'system-2',
    focus: 'System Design',
    prompt: 'Design an application tracker that supports reminders, scorecards, and pipeline analytics.',
    evidence: 'State machine, event log, user_id filtering, reminder calculation, UX states.',
    followUp: 'How would you keep the tracker useful without allowing auto-apply behavior?',
  },
  {
    id: 'rag-1',
    focus: 'AI/RAG',
    prompt: 'How would you evaluate groundedness for a resume rewrite or recruiter draft?',
    evidence: 'Golden cases, citation checks, forbidden-claim tests, compliance block rate.',
    followUp: 'What should happen when the model has insufficient evidence?',
  },
  {
    id: 'rag-2',
    focus: 'AI/RAG',
    prompt: 'Explain how you would route local and external model calls in a privacy-first AI app.',
    evidence: 'Gateway abstraction, provider settings, consent record, redaction service, audit row.',
    followUp: 'What data is allowed to leave the machine, and under what conditions?',
  },
  {
    id: 'backend-1',
    focus: 'Backend',
    prompt: 'Walk through a FastAPI endpoint that must enforce user isolation and audit every AI request.',
    evidence: 'Dependency injection, authenticated user_id, service boundary, request_id propagation.',
    followUp: 'Which tests would catch a cross-user data leak?',
  },
  {
    id: 'backend-2',
    focus: 'Backend',
    prompt: 'How would you design immutable resume uploads and role-specific resume versions?',
    evidence: 'Storage key strategy, version table, parser output, original-preservation rule.',
    followUp: 'What would you never delete or overwrite?',
  },
  {
    id: 'leadership-1',
    focus: 'Leadership',
    prompt: 'Tell me about a technical decision where you optimized for safety over speed.',
    evidence: 'Risk register, acceptance criteria, compliance checklist, rollout decision.',
    followUp: 'How did you explain the tradeoff to non-technical stakeholders?',
  },
  {
    id: 'leadership-2',
    focus: 'Leadership',
    prompt: 'Describe how you would lead a small team through a layoff-to-offer product launch.',
    evidence: 'Prior planning cadence, scope tradeoffs, quality gates, ownership model.',
    followUp: 'What would you cut first if the timeline compressed?',
  },
];

function parseAttempts(raw: string | null) {
  if (!raw) return [] as Attempt[];

  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((attempt): attempt is Attempt => {
      return (
        typeof attempt?.id === 'string' &&
        typeof attempt.prompt === 'string' &&
        FOCUS_AREAS.includes(attempt.focus) &&
        typeof attempt.score === 'number'
      );
    });
  } catch {
    return [];
  }
}

export default function InterviewPrep() {
  const [focus, setFocus] = useState<FocusArea>('System Design');
  const [questionIndex, setQuestionIndex] = useState(0);
  const [notes, setNotes] = useState('');
  const [checks, setChecks] = useState<Record<CheckName, boolean>>({
    'STAR structure': true,
    'Specific project evidence': true,
    'Named tradeoff': false,
    'No fabricated metric': true,
    'Clear boundary': false,
  });
  const [clarity, setClarity] = useState(3);
  const [depth, setDepth] = useState(3);
  const [attempts, setAttempts] = useState<Attempt[]>([]);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    setAttempts(parseAttempts(window.localStorage.getItem(STORAGE_KEY)));
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (!isHydrated) return;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(attempts));
  }, [attempts, isHydrated]);

  const focusedQuestions = useMemo(() => QUESTIONS.filter((question) => question.focus === focus), [focus]);
  const currentQuestion = focusedQuestions[questionIndex % focusedQuestions.length];
  const checkedCount = CHECKS.filter((check) => checks[check]).length;
  const score = Math.round((checkedCount / CHECKS.length) * 60 + ((clarity + depth) / 10) * 40);

  function nextQuestion() {
    setQuestionIndex((current) => (current + 1) % focusedQuestions.length);
    setNotes('');
  }

  function saveAttempt() {
    setAttempts((current) => [
      {
        id: `attempt-${Date.now()}`,
        prompt: currentQuestion.prompt,
        focus,
        score,
        notes,
        savedAt: new Date().toISOString().slice(0, 10),
      },
      ...current.slice(0, 7),
    ]);
  }

  function resetPractice() {
    setNotes('');
    setClarity(3);
    setDepth(3);
    setChecks({
      'STAR structure': true,
      'Specific project evidence': true,
      'Named tradeoff': false,
      'No fabricated metric': true,
      'Clear boundary': false,
    });
  }

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Interview prep"
        title="Practice with evidence and boundaries"
        description="Use focused question sets, self-scoring, and local attempt history to tighten answers before interviews."
        actions={
          <span className="pill border-emerald-900 bg-emerald-950 text-emerald-300">
            <CheckCircle2 className="h-3.5 w-3.5" /> Evidence first
          </span>
        }
      />

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <MetricCard label="Focus" value={focus} detail={`${focusedQuestions.length} prompts in this set`} icon={SlidersHorizontal} tone="text-cyan-300" />
        <MetricCard label="Current score" value={`${score}/100`} detail={`${checkedCount}/${CHECKS.length} evidence checks`} icon={ClipboardList} tone={score >= 75 ? 'text-emerald-300' : 'text-amber-300'} />
        <MetricCard label="Saved attempts" value={attempts.length} detail="stored locally in this browser" icon={History} tone="text-violet-300" />
      </section>

      <section className="card">
        <SectionHeader title="Focus area" description="Switch sets without losing saved attempts." />
        <div className="flex flex-wrap gap-2">
          {FOCUS_AREAS.map((area) => (
            <button
              key={area}
              className={`btn ${focus === area ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => {
                setFocus(area);
                setQuestionIndex(0);
                setNotes('');
              }}
            >
              {area}
            </button>
          ))}
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="card">
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <div className="text-xs uppercase tracking-wide text-cyan-300">{currentQuestion.focus}</div>
              <h2 className="mt-2 text-2xl font-semibold leading-snug text-white">{currentQuestion.prompt}</h2>
            </div>
            <span className="pill border-zinc-800 bg-zinc-950 text-zinc-300">{score}/100</span>
          </div>

          <div className="mb-5">
            <ProgressBar value={score} tone={score >= 75 ? 'bg-emerald-300' : 'bg-amber-300'} label="answer readiness" />
          </div>

          <dl className="grid grid-cols-1 gap-4 text-sm md:grid-cols-2">
            <div>
              <dt className="text-zinc-500">Evidence to cite</dt>
              <dd className="mt-1 text-zinc-300">{currentQuestion.evidence}</dd>
            </div>
            <div>
              <dt className="text-zinc-500">Likely follow-up</dt>
              <dd className="mt-1 text-zinc-300">{currentQuestion.followUp}</dd>
            </div>
          </dl>

          <label className="mt-6 block text-sm">
            <span className="mb-2 block text-zinc-400">Answer notes</span>
            <textarea
              className="input h-56"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Draft your answer with concrete evidence and explicit boundaries."
            />
          </label>

          <div className="mt-5 flex flex-wrap gap-2">
            <button className="btn btn-primary" onClick={saveAttempt} disabled={!notes.trim()}>
              <Save className="h-4 w-4" /> Save attempt
            </button>
            <button className="btn btn-secondary" onClick={nextQuestion}>
              <ArrowRight className="h-4 w-4" /> Next
            </button>
            <button className="btn btn-secondary" onClick={resetPractice}>
              <RotateCcw className="h-4 w-4" /> Reset
            </button>
          </div>
        </div>

        <div className="space-y-4">
          <section className="card">
            <SectionHeader title="Evidence checklist" description="The answer should stay specific and bounded." />
            <div className="space-y-3">
              {CHECKS.map((check) => (
                <label key={check} className="flex items-center justify-between gap-3 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm">
                  <span>{check}</span>
                  <input
                    type="checkbox"
                    checked={checks[check]}
                    onChange={(event) => setChecks((current) => ({ ...current, [check]: event.target.checked }))}
                  />
                </label>
              ))}
            </div>
          </section>

          <section className="card">
            <SectionHeader title="Self score" description="Local practice signal, not a hiring prediction." />
            <label className="block text-sm">
              <span className="mb-2 flex items-center justify-between text-zinc-400">
                Clarity <span>{clarity}/5</span>
              </span>
              <input className="w-full" type="range" min={1} max={5} value={clarity} onChange={(event) => setClarity(Number(event.target.value))} />
            </label>
            <label className="mt-5 block text-sm">
              <span className="mb-2 flex items-center justify-between text-zinc-400">
                Technical depth <span>{depth}/5</span>
              </span>
              <input className="w-full" type="range" min={1} max={5} value={depth} onChange={(event) => setDepth(Number(event.target.value))} />
            </label>
            <div className="disclaimer mt-5">Scores are local practice signals, not hiring predictions.</div>
          </section>
        </div>
      </section>

      <section className="card">
        <SectionHeader
          title="Recent attempts"
          description="A lightweight record of practice loops completed on this device."
          action={<span className="text-xs text-zinc-500">{attempts.length} saved</span>}
        />
        {attempts.length ? (
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-4">
            {attempts.map((attempt) => (
              <article key={attempt.id} className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs text-cyan-300">{attempt.focus}</span>
                  <span className="text-sm font-medium text-white">{attempt.score}</span>
                </div>
                <h3 className="mt-3 line-clamp-3 text-sm text-zinc-200">{attempt.prompt}</h3>
                <p className="mt-3 text-xs text-zinc-500">{attempt.savedAt}</p>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState icon={MessageSquareText} title="No attempts saved yet" description="Write notes for a prompt and save the attempt to start a local practice history." />
        )}
      </section>
    </div>
  );
}
