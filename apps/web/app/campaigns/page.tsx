'use client';

import React, { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  FileText,
  Gauge,
  ListChecks,
  LockKeyhole,
  Play,
  RefreshCcw,
  ShieldCheck,
  Sparkles,
  UserCheck,
  XCircle,
} from 'lucide-react';
import { toast } from 'sonner';
import { apiFetch, getStoredToken } from '@/lib/api';
import { EmptyState, MetricCard, PageHeader, SectionHeader, SafetyNotice } from '@/components/product-ui';

type Campaign = {
  id: string;
  goal: string;
  status: string;
  metadata_json?: Record<string, unknown> | null;
  created_at: string;
  updated_at?: string | null;
};

type Quality = {
  ai_confidence?: number;
  groundedness_score?: number;
  evidence_count?: number;
  citation_count?: number;
  missing_evidence_count?: number;
  compliance_passed?: boolean;
  approval_required?: boolean;
  scoring_note?: string;
};

type CampaignTask = {
  id: string;
  title: string;
  owner: string;
  description: string;
  status: string;
  citations?: string[];
};

type Artifact = {
  artifact_type: string;
  title: string;
  content: Record<string, unknown>;
  citations?: string[];
  ai_confidence?: number;
  groundedness_score?: number;
  quality_signals?: Quality;
  requires_human_approval?: boolean;
};

type EvidenceItem = {
  source: string;
  citation: string;
  text: string;
  validated: boolean;
};

type CampaignRun = {
  campaign_id: string;
  status: string;
  thread_id: string;
  checkpoint_backend: string;
  ai_confidence: number;
  groundedness_score: number;
  quality: Quality;
  plan: CampaignTask[];
  artifacts: Artifact[];
  approvals: Array<Record<string, unknown>>;
  compliance: Record<string, unknown>;
  evidence: EvidenceItem[];
  warnings: string[];
  errors: string[];
  next_actions: string[];
  langsmith: Record<string, unknown>;
  deepagents: Record<string, unknown>;
};

type Approval = {
  id: string;
  campaign_id: string;
  artifact_type: string;
  artifact_json?: Record<string, unknown> | null;
  status: string;
  notes?: string | null;
  responded_at?: string | null;
  created_at: string;
};

const DEFAULT_GOAL =
  'Build a grounded Staff AI / backend engineering campaign using my uploaded resume evidence, without fabricating metrics or auto-sending outreach.';

function statusClass(status: string) {
  if (['approved', 'completed', 'Done', 'completed'].includes(status)) {
    return 'border-emerald-900 bg-emerald-950/40 text-emerald-300';
  }
  if (['blocked', 'failed', 'rejected'].includes(status)) {
    return 'border-red-900 bg-red-950/40 text-red-300';
  }
  if (['awaiting_approval', 'pending', 'running'].includes(status)) {
    return 'border-amber-900 bg-amber-950/40 text-amber-300';
  }
  return 'border-zinc-800 bg-zinc-950 text-zinc-300';
}

function scoreTone(score = 0) {
  if (score >= 0.75) return 'text-emerald-300';
  if (score >= 0.5) return 'text-amber-300';
  return 'text-red-300';
}

function percent(score?: number) {
  return Math.round((score || 0) * 100);
}

function splitList(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function isCampaignRun(value: CampaignRun | Campaign): value is CampaignRun {
  return 'campaign_id' in value && 'plan' in value;
}

function stateFromCampaign(campaign: Campaign | undefined): CampaignRun | null {
  const metadata = campaign?.metadata_json || {};
  const lastState = metadata.last_state as Partial<CampaignRun> | undefined;
  if (!campaign || !lastState) return null;
  const quality = (lastState.quality || {}) as Quality;
  return {
    campaign_id: campaign.id,
    status: String(lastState.status || campaign.status),
    thread_id: String(metadata.thread_id || ''),
    checkpoint_backend: String(metadata.checkpoint_backend || 'memory'),
    ai_confidence: Number(lastState.ai_confidence || quality.ai_confidence || 0),
    groundedness_score: Number(lastState.groundedness_score || quality.groundedness_score || 0),
    quality,
    plan: (lastState.plan || []) as CampaignTask[],
    artifacts: (lastState.artifacts || []) as Artifact[],
    approvals: (lastState.approvals || []) as Array<Record<string, unknown>>,
    compliance: (lastState.compliance || {}) as Record<string, unknown>,
    evidence: (lastState.evidence || []) as EvidenceItem[],
    warnings: (lastState.warnings || []) as string[],
    errors: (lastState.errors || []) as string[],
    next_actions: (lastState.next_actions || []) as string[],
    langsmith: (metadata.langsmith || {}) as Record<string, unknown>,
    deepagents: (metadata.deepagents || {}) as Record<string, unknown>,
  };
}

function stringifyValue(value: unknown) {
  if (Array.isArray(value)) return value.map((item) => String(item)).join('\n');
  if (value && typeof value === 'object') return JSON.stringify(value, null, 2);
  return String(value || '');
}

function QualityMeter({ label, score }: { label: string; score?: number }) {
  const pct = percent(score);
  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3 text-xs">
        <span className="text-zinc-400">{label}</span>
        <span className={`font-semibold ${scoreTone(score)}`}>{pct}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-zinc-950">
        <div className="h-full bg-white" style={{ width: `${Math.min(100, Math.max(0, pct))}%` }} />
      </div>
    </div>
  );
}

export default function Campaigns() {
  const queryClient = useQueryClient();
  const [token] = useState(() => getStoredToken());
  const [goal, setGoal] = useState(DEFAULT_GOAL);
  const [targetRoles, setTargetRoles] = useState('Staff AI Engineer, Senior Backend Engineer');
  const [constraints, setConstraints] = useState('Local AI only, manual outreach, cite resume evidence');
  const [activeRun, setActiveRun] = useState<CampaignRun | null>(null);
  const [selectedCampaignId, setSelectedCampaignId] = useState<string | null>(null);
  const [approvalNotes, setApprovalNotes] = useState<Record<string, string>>({});

  const campaignsQuery = useQuery({
    queryKey: ['agent-campaigns'],
    queryFn: () => apiFetch<Campaign[]>('/api/v1/agents/campaigns'),
    enabled: Boolean(token),
  });

  const approvalsQuery = useQuery({
    queryKey: ['agent-approvals'],
    queryFn: () => apiFetch<Approval[]>('/api/v1/agents/approvals'),
    enabled: Boolean(token),
  });

  const createCampaign = useMutation({
    mutationFn: () =>
      apiFetch<CampaignRun | Campaign>('/api/v1/agents/campaigns', {
        method: 'POST',
        body: JSON.stringify({
          goal,
          target_roles: splitList(targetRoles),
          constraints: splitList(constraints),
          run_immediately: true,
        }),
      }),
    onSuccess: (data) => {
      if (isCampaignRun(data)) {
        setActiveRun(data);
        setSelectedCampaignId(data.campaign_id);
      }
      queryClient.invalidateQueries({ queryKey: ['agent-campaigns'] });
      queryClient.invalidateQueries({ queryKey: ['agent-approvals'] });
      toast.success('Campaign run created');
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Campaign run failed');
    },
  });

  const decideApproval = useMutation({
    mutationFn: ({ id, status }: { id: string; status: 'approved' | 'rejected' }) =>
      apiFetch<Approval>(`/api/v1/agents/approvals/${id}/decide`, {
        method: 'POST',
        body: JSON.stringify({
          status,
          notes: approvalNotes[id] || (status === 'approved' ? 'Approved in campaign cockpit.' : 'Needs edits before use.'),
        }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-campaigns'] });
      queryClient.invalidateQueries({ queryKey: ['agent-approvals'] });
      toast.success('Approval updated');
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : 'Approval update failed');
    },
  });

  const selectedCampaign = useMemo(() => {
    const campaigns = campaignsQuery.data || [];
    if (selectedCampaignId) return campaigns.find((item) => item.id === selectedCampaignId);
    return campaigns[0];
  }, [campaignsQuery.data, selectedCampaignId]);

  const displayedRun = activeRun && activeRun.campaign_id === selectedCampaignId ? activeRun : stateFromCampaign(selectedCampaign);
  const approvals = approvalsQuery.data || [];
  const pendingApprovals = approvals.filter((approval) => approval.status === 'pending');
  const quality = displayedRun?.quality || {};
  const compliancePassed = Boolean(displayedRun?.compliance?.passed);

  if (!token) {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Campaign cockpit"
          title="Supervised agent runs need authentication"
          description="Campaigns create user-isolated plans, cited draft artifacts, and approval checkpoints tied to a JWT-backed API session."
          actions={
            <span className="pill border-amber-400/20 bg-amber-400/10 text-amber-100">
              <LockKeyhole className="h-3.5 w-3.5" /> Login required
            </span>
          }
        />
        <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <MetricCard label="Artifacts" value="Drafts" detail="never sent automatically" icon={FileText} tone="text-cyan-300" />
          <MetricCard label="Approvals" value="Manual" detail="human checkpoint required" icon={UserCheck} tone="text-emerald-300" />
          <MetricCard label="Audit" value="Required" detail="agent and AI events logged" icon={ClipboardCheck} tone="text-amber-300" />
        </section>
        <section className="card max-w-2xl">
          <SectionHeader title="Start a guarded session" description="Use the demo login to create or reuse a local authenticated user." />
          <a href="/login" className="btn btn-primary mt-4">
            Login / Create Demo User
          </a>
        </section>
        <SafetyNotice tone="warning">
          Campaign agents draft only. They do not auto-apply, auto-send outreach, or override deterministic services.
        </SafetyNotice>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Campaign cockpit"
        title="Supervised career campaign"
        description="LangGraph supervisor, Deep Agent roles, citations, compliance checks, and explicit approval checkpoints."
        actions={
          <>
          <span className="pill border-emerald-900 bg-emerald-950 text-emerald-300">
            <ShieldCheck className="h-3.5 w-3.5" /> No auto-send
          </span>
          <span className={`pill ${statusClass(displayedRun?.status || selectedCampaign?.status || 'created')}`}>
            {displayedRun?.status || selectedCampaign?.status || 'No run'}
          </span>
          </>
        }
      />

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="card">
          <SectionHeader title="Campaign input" description="Give the agent a goal and hard constraints it must preserve." />
          <label className="text-sm">
            <span className="mb-2 block text-zinc-400">Goal</span>
            <textarea className="input h-28" value={goal} onChange={(event) => setGoal(event.target.value)} />
          </label>
          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="text-sm">
              <span className="mb-2 block text-zinc-400">Target roles</span>
              <input className="input" value={targetRoles} onChange={(event) => setTargetRoles(event.target.value)} />
            </label>
            <label className="text-sm">
              <span className="mb-2 block text-zinc-400">Constraints</span>
              <input className="input" value={constraints} onChange={(event) => setConstraints(event.target.value)} />
            </label>
          </div>
          <div className="mt-5 flex flex-wrap gap-2">
            <button className="btn btn-primary" onClick={() => createCampaign.mutate()} disabled={createCampaign.isPending || goal.length < 10}>
              <Play className="h-4 w-4" /> {createCampaign.isPending ? 'Running...' : 'Run supervised campaign'}
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => {
                campaignsQuery.refetch();
                approvalsQuery.refetch();
              }}
            >
              <RefreshCcw className="h-4 w-4" /> Refresh
            </button>
          </div>
          <div className="disclaimer mt-4">
            Runs draft artifacts only. Approval does not send messages or apply to jobs.
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="card">
            <div className="flex items-center gap-2 text-sm text-zinc-400">
              <Gauge className="h-4 w-4 text-cyan-300" /> AI confidence
            </div>
            <div className={`metric mt-3 ${scoreTone(displayedRun?.ai_confidence)}`}>{percent(displayedRun?.ai_confidence)}%</div>
            <div className="mt-4">
              <QualityMeter label="Groundedness" score={displayedRun?.groundedness_score} />
            </div>
          </div>
          <div className="card">
            <div className="text-sm text-zinc-400">Grounding signals</div>
            <dl className="mt-4 grid grid-cols-3 gap-3 text-sm">
              <div>
                <dt className="text-xs text-zinc-500">Evidence</dt>
                <dd className="mt-1 text-white">{quality.evidence_count || 0}</dd>
              </div>
              <div>
                <dt className="text-xs text-zinc-500">Citations</dt>
                <dd className="mt-1 text-white">{quality.citation_count || 0}</dd>
              </div>
              <div>
                <dt className="text-xs text-zinc-500">Missing</dt>
                <dd className="mt-1 text-white">{quality.missing_evidence_count || 0}</dd>
              </div>
            </dl>
            <div className={`mt-4 flex items-center gap-2 text-sm ${compliancePassed ? 'text-emerald-300' : 'text-amber-300'}`}>
              {compliancePassed ? <CheckCircle2 className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
              Compliance {compliancePassed ? 'passed' : 'pending or blocked'}
            </div>
          </div>
          <div className="card">
            <div className="text-sm text-zinc-400">Approval queue</div>
            <div className="metric mt-3 text-amber-300">{pendingApprovals.length}</div>
            <div className="mt-2 text-xs text-zinc-500">{approvals.length} total checkpoints</div>
          </div>
          <div className="card">
            <div className="text-sm text-zinc-400">Backend runtime</div>
            <div className="mt-3 text-sm text-zinc-300">{displayedRun?.checkpoint_backend || 'memory'} checkpoint</div>
            <div className="mt-2 break-words text-xs text-zinc-500">
              LangSmith: {String(displayedRun?.langsmith?.project || 'reboundiq-local')}
            </div>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[0.78fr_1.22fr]">
        <div className="space-y-6">
          <section className="card">
            <SectionHeader title="Recent campaigns" description="Select a prior run to inspect stored state and approvals." />
            <div className="space-y-2">
              {(campaignsQuery.data || []).map((campaign) => (
                <button
                  key={campaign.id}
                  className={`w-full rounded-lg border p-3 text-left text-sm transition-colors ${
                    campaign.id === selectedCampaign?.id ? 'border-zinc-500 bg-zinc-800' : 'border-zinc-800 bg-zinc-950 hover:border-zinc-700'
                  }`}
                  onClick={() => {
                    setSelectedCampaignId(campaign.id);
                    setActiveRun(null);
                  }}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="line-clamp-1 font-medium text-white">{campaign.goal}</span>
                    <span className={`pill ${statusClass(campaign.status)}`}>{campaign.status}</span>
                  </div>
                  <div className="mt-2 text-xs text-zinc-500">{campaign.id}</div>
                </button>
              ))}
              {!campaignsQuery.data?.length && <EmptyState icon={ListChecks} title="No campaigns yet" description="Run a supervised campaign to create a plan, draft artifacts, and approval checkpoints." />}
            </div>
          </section>

          <section className="card">
            <SectionHeader title="Evidence" description="Validated source snippets available to this campaign state." />
            <div className="space-y-3">
              {(displayedRun?.evidence || []).map((item) => (
                <article key={`${item.citation}-${item.source}`} className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                  <div className="flex items-center justify-between gap-3 text-xs">
                    <span className="text-zinc-300">{item.citation}</span>
                    <span className={item.validated ? 'text-emerald-300' : 'text-amber-300'}>{item.validated ? 'validated' : 'review'}</span>
                  </div>
                  <p className="mt-2 line-clamp-4 text-xs text-zinc-500">{item.text}</p>
                </article>
              ))}
              {!displayedRun?.evidence?.length && <EmptyState icon={Sparkles} title="No evidence loaded" description="Run a campaign after uploading source material to populate validated evidence." />}
            </div>
          </section>
        </div>

        <div className="space-y-6">
          <section className="card">
            <SectionHeader title="Workflow plan" description="Agent-authored plan steps remain suggestions until reviewed." />
            <ol className="space-y-4">
              {(displayedRun?.plan || []).map((step, index) => (
                <li key={step.id || step.title} className="flex gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-zinc-800 bg-zinc-950 text-xs">
                    {index + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h2 className="font-medium text-white">{step.title}</h2>
                      <span className={`pill ${statusClass(step.status)}`}>{step.status}</span>
                    </div>
                    <p className="mt-1 text-sm text-zinc-400">{step.description}</p>
                    <p className="mt-1 text-xs text-zinc-500">
                      {step.owner} {step.citations?.length ? `• ${step.citations.join(', ')}` : ''}
                    </p>
                  </div>
                </li>
              ))}
              {!displayedRun?.plan?.length && (
                <li className="list-none">
                  <EmptyState icon={Play} title="No plan generated" description="Run a campaign to generate a supervised plan from the current goal and constraints." />
                </li>
              )}
            </ol>
          </section>

          <section className="card">
            <SectionHeader title="Draft artifacts" description="Generated content remains review-only and citation-bearing." />
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {(displayedRun?.artifacts || []).map((artifact) => (
                <article key={`${artifact.artifact_type}-${artifact.title}`} className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h2 className="font-medium text-white">{artifact.title}</h2>
                      <div className="mt-1 text-xs text-zinc-500">{artifact.artifact_type.replaceAll('_', ' ')}</div>
                    </div>
                    <span className="pill border-amber-900 bg-amber-950/40 text-amber-300">Needs review</span>
                  </div>
                  <div className="mt-4 grid grid-cols-1 gap-3">
                    <QualityMeter label="AI confidence" score={artifact.ai_confidence} />
                    <QualityMeter label="Groundedness" score={artifact.groundedness_score} />
                  </div>
                  <div className="mt-4 space-y-3 text-sm">
                    {Object.entries(artifact.content || {})
                      .filter(([key]) => !['manual_review_required', 'planning_guidance_only'].includes(key))
                      .slice(0, 4)
                      .map(([key, value]) => (
                        <div key={key}>
                          <div className="text-xs uppercase text-zinc-500">{key.replaceAll('_', ' ')}</div>
                          <div className="mt-1 whitespace-pre-wrap text-zinc-300">{stringifyValue(value)}</div>
                        </div>
                      ))}
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {(artifact.citations || []).map((citation) => (
                      <span key={citation} className="pill border-zinc-800 bg-zinc-900 text-zinc-300">
                        {citation}
                      </span>
                    ))}
                  </div>
                </article>
              ))}
              {!displayedRun?.artifacts?.length && <EmptyState icon={FileText} title="No artifacts drafted" description="Artifacts will appear here after the campaign has enough grounded source evidence." />}
            </div>
          </section>
        </div>
      </section>

      <section className="card">
        <SectionHeader title="Human approval checkpoints" description="Approving an artifact does not send it or apply it anywhere." />
        <div className="space-y-4">
          {approvals.map((approval) => (
            <article key={approval.id} className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="font-medium text-white">{approval.artifact_type.replaceAll('_', ' ')}</h2>
                    <span className={`pill ${statusClass(approval.status)}`}>{approval.status}</span>
                  </div>
                  <p className="mt-2 text-xs text-zinc-500">{approval.id}</p>
                </div>
              </div>
              <textarea
                className="input mt-4 h-20"
                value={approvalNotes[approval.id] || ''}
                onChange={(event) => setApprovalNotes((current) => ({ ...current, [approval.id]: event.target.value }))}
                placeholder="Decision notes"
                disabled={approval.status !== 'pending'}
              />
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  className="btn btn-primary px-3 py-1.5"
                  onClick={() => decideApproval.mutate({ id: approval.id, status: 'approved' })}
                  disabled={approval.status !== 'pending' || decideApproval.isPending}
                >
                  <UserCheck className="h-4 w-4" /> Approve
                </button>
                <button
                  className="btn btn-secondary px-3 py-1.5"
                  onClick={() => decideApproval.mutate({ id: approval.id, status: 'rejected' })}
                  disabled={approval.status !== 'pending' || decideApproval.isPending}
                >
                  <XCircle className="h-4 w-4" /> Reject
                </button>
              </div>
            </article>
          ))}
          {!approvals.length && <EmptyState icon={ClipboardCheck} title="No checkpoints yet" description="Approval records are created when a campaign drafts reviewable artifacts." />}
        </div>
      </section>
    </div>
  );
}
