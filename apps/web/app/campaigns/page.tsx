'use client';

import React, { useMemo, useState } from 'react';
import { Bot, CirclePause, ClipboardCheck, FileText, Play, ShieldCheck, Sparkles, UserCheck } from 'lucide-react';

type CampaignGoal = 'AI Platform Search' | 'Backend Systems Search' | 'Leadership Search';
type ApprovalStatus = 'Needs review' | 'Approved' | 'Needs edits';

type Approval = {
  id: string;
  title: string;
  artifactType: string;
  owner: string;
  status: ApprovalStatus;
  source: string;
};

const GOALS: CampaignGoal[] = ['AI Platform Search', 'Backend Systems Search', 'Leadership Search'];

const BASE_APPROVALS: Approval[] = [
  {
    id: 'approval-1',
    title: 'AI platform resume summary',
    artifactType: 'Resume version',
    owner: 'ResumeDeep',
    status: 'Needs review',
    source: 'Uploaded resume and JD match notes',
  },
  {
    id: 'approval-2',
    title: 'Recruiter follow-up draft',
    artifactType: 'Outreach draft',
    owner: 'OutreachDeep',
    status: 'Needs edits',
    source: 'Application tracker and saved JD snapshot',
  },
  {
    id: 'approval-3',
    title: 'System design prep sheet',
    artifactType: 'Interview prep',
    owner: 'InterviewDeep',
    status: 'Approved',
    source: 'Proof asset and target role gaps',
  },
];

const WORKFLOW_STEPS = [
  { name: 'Validate user data', owner: 'PlannerDeep', status: 'Done' },
  { name: 'Rank target roles', owner: 'JDDeep', status: 'Done' },
  { name: 'Draft grounded artifacts', owner: 'ResumeDeep / ProofDeep', status: 'In review' },
  { name: 'Human approval checkpoint', owner: 'ComplianceGuardAgent', status: 'Waiting' },
  { name: 'Manual action only', owner: 'User', status: 'Locked' },
];

function statusClass(status: string) {
  if (status === 'Approved' || status === 'Done') return 'border-emerald-900 bg-emerald-950/40 text-emerald-300';
  if (status === 'Needs edits' || status === 'In review' || status === 'Waiting') return 'border-amber-900 bg-amber-950/40 text-amber-300';
  return 'border-zinc-800 bg-zinc-950 text-zinc-300';
}

export default function Campaigns() {
  const [goal, setGoal] = useState<CampaignGoal>('AI Platform Search');
  const [approvals, setApprovals] = useState<Approval[]>(BASE_APPROVALS);

  const metrics = useMemo(() => {
    return {
      total: approvals.length,
      approved: approvals.filter((approval) => approval.status === 'Approved').length,
      waiting: approvals.filter((approval) => approval.status !== 'Approved').length,
    };
  }, [approvals]);

  function setApprovalStatus(id: string, status: ApprovalStatus) {
    setApprovals((current) => current.map((approval) => (approval.id === id ? { ...approval, status } : approval)));
  }

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Career Campaigns</h1>
          <p className="mt-1 text-sm text-zinc-400">Supervised workflow planning with explicit human checkpoints.</p>
        </div>
        <span className="pill border-emerald-900 bg-emerald-950 text-emerald-300">
          <ShieldCheck className="h-3.5 w-3.5" /> Never auto-apply
        </span>
      </header>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="card">
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            <Bot className="h-4 w-4 text-cyan-300" /> Campaign goal
          </div>
          <select className="input mt-4" value={goal} onChange={(event) => setGoal(event.target.value as CampaignGoal)}>
            {GOALS.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </div>
        <div className="card">
          <div className="text-sm text-zinc-400">Approval queue</div>
          <div className="metric mt-3 text-amber-300">{metrics.waiting}</div>
          <div className="mt-2 text-xs text-zinc-500">{metrics.total} total artifacts</div>
        </div>
        <div className="card">
          <div className="text-sm text-zinc-400">Approved artifacts</div>
          <div className="metric mt-3 text-emerald-300">{metrics.approved}</div>
          <div className="mt-2 text-xs text-zinc-500">Approved still require manual user action.</div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="card">
          <div className="mb-4 flex items-center gap-2 text-sm text-zinc-400">
            <Play className="h-4 w-4" /> Workflow
          </div>
          <ol className="space-y-4">
            {WORKFLOW_STEPS.map((step, index) => (
              <li key={step.name} className="flex gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-zinc-800 bg-zinc-950 text-xs">
                  {index + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h2 className="font-medium text-white">{step.name}</h2>
                    <span className={`pill ${statusClass(step.status)}`}>{step.status}</span>
                  </div>
                  <p className="mt-1 text-sm text-zinc-500">{step.owner}</p>
                </div>
              </li>
            ))}
          </ol>
          <div className="disclaimer mt-5">
            Deep agents orchestrate deterministic services. They do not fabricate claims, auto-send messages, or apply changes without approval.
          </div>
        </div>

        <div className="card">
          <div className="mb-4 flex items-center gap-2 text-sm text-zinc-400">
            <ClipboardCheck className="h-4 w-4" /> Human approval queue
          </div>
          <div className="space-y-4">
            {approvals.map((approval) => (
              <article key={approval.id} className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="font-medium text-white">{approval.title}</h2>
                      <span className={`pill ${statusClass(approval.status)}`}>{approval.status}</span>
                    </div>
                    <dl className="mt-3 grid grid-cols-1 gap-3 text-sm md:grid-cols-3">
                      <div>
                        <dt className="text-xs text-zinc-500">Artifact</dt>
                        <dd className="mt-1 text-zinc-300">{approval.artifactType}</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-zinc-500">Owner</dt>
                        <dd className="mt-1 text-zinc-300">{approval.owner}</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-zinc-500">Source</dt>
                        <dd className="mt-1 text-zinc-300">{approval.source}</dd>
                      </div>
                    </dl>
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <button className="btn btn-secondary px-3 py-1.5" onClick={() => setApprovalStatus(approval.id, 'Needs edits')}>
                    <CirclePause className="h-4 w-4" /> Needs edits
                  </button>
                  <button className="btn btn-primary px-3 py-1.5" onClick={() => setApprovalStatus(approval.id, 'Approved')}>
                    <UserCheck className="h-4 w-4" /> Approve
                  </button>
                  <button className="btn btn-secondary px-3 py-1.5" onClick={() => setApprovalStatus(approval.id, 'Needs review')}>
                    <FileText className="h-4 w-4" /> Review
                  </button>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="card">
        <div className="mb-4 flex items-center gap-2 text-sm text-zinc-400">
          <Sparkles className="h-4 w-4" /> Campaign brief
        </div>
        <div className="grid grid-cols-1 gap-4 text-sm md:grid-cols-3">
          <div>
            <h2 className="font-medium text-white">{goal}</h2>
            <p className="mt-2 text-zinc-400">Target roles are ranked from user-provided evidence and saved JD snapshots.</p>
          </div>
          <div>
            <h2 className="font-medium text-white">Compliance gates</h2>
            <p className="mt-2 text-zinc-400">Approval, consent, citations, and disclaimers remain visible before artifacts are used.</p>
          </div>
          <div>
            <h2 className="font-medium text-white">Manual execution</h2>
            <p className="mt-2 text-zinc-400">Applications, messages, and profile edits stay under user control.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
