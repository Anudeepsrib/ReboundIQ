'use client';

import React, { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, Clipboard, FileCheck2, LockKeyhole, Save, ShieldCheck, Trash2, Trophy } from 'lucide-react';
import { apiFetch, getStoredToken } from '@/lib/api';
import { EmptyState, MetricCard, PageHeader, ProgressBar, SectionHeader } from '@/components/product-ui';

const ASSET_TYPES = [
  ['star_story', 'STAR story'],
  ['case_study', 'Case study'],
  ['architecture_note', 'Architecture note'],
  ['github_readme', 'GitHub README'],
  ['linkedin_post', 'LinkedIn post'],
] as const;

type ProofAsset = {
  id: string;
  title: string;
  asset_type: string;
  status: string;
  summary?: string | null;
  content_json?: Record<string, unknown> | null;
  citations_json?: Array<string | Record<string, unknown>> | null;
  metadata_json?: Record<string, unknown> | null;
  created_at: string;
};

type Draft = {
  title: string;
  asset_type: string;
  target_role: string;
  source_evidence: string;
  situation: string;
  task: string;
  action: string;
  result: string;
  metric: string;
  citations: string;
};

const DEFAULT_DRAFT: Draft = {
  title: 'Privacy-first AI gateway rollout',
  asset_type: 'architecture_note',
  target_role: 'Senior AI Platform Engineer',
  source_evidence: 'Design doc, gateway implementation notes, eval results, audit log schema.',
  situation: 'The product needed AI-assisted career workflows without exposing personal data by default.',
  task: 'Design a provider-neutral path where local Ollama remained the default and external providers required consent.',
  action: 'Introduced a single AI gateway, redaction checks, compliance review, and audit records.',
  result: 'The system supported resume and JD workflows while preserving user isolation and manual approval.',
  metric: '',
  citations: 'README local-first policy; AGENTS.md non-negotiables; ai_requests schema.',
};

function assetLabel(value: string) {
  return ASSET_TYPES.find(([key]) => key === value)?.[1] || value.replaceAll('_', ' ');
}

function coverageForDraft(draft: Draft) {
  const fields: Array<keyof Draft> = ['title', 'target_role', 'source_evidence', 'situation', 'task', 'action', 'result', 'citations'];
  return Math.round((fields.filter((field) => String(draft[field]).trim()).length / fields.length) * 100);
}

function buildDraftText(draft: Draft) {
  const metric = draft.metric.trim() || 'Metric not provided; keep this claim qualitative until evidence exists.';
  return `${draft.title || 'Proof Asset'}

Target role
${draft.target_role || 'Target role missing.'}

Situation
${draft.situation || 'Situation evidence missing.'}

Task
${draft.task || 'Task evidence missing.'}

Action
${draft.action || 'Action evidence missing.'}

Result
${draft.result || 'Result evidence missing.'}

Evidence
${draft.source_evidence || 'Evidence sources missing.'}

Metric / boundary
${metric}

Citations
${draft.citations || 'Citations missing.'}`;
}

export default function ProofBuilder() {
  const queryClient = useQueryClient();
  const [token] = useState(() => getStoredToken());
  const [draft, setDraft] = useState<Draft>(DEFAULT_DRAFT);
  const [copied, setCopied] = useState(false);

  const assetsQuery = useQuery({
    queryKey: ['proof-assets'],
    queryFn: () => apiFetch<ProofAsset[]>('/api/v1/proof/assets'),
    enabled: Boolean(token),
  });

  const coverage = useMemo(() => coverageForDraft(draft), [draft]);
  const draftText = useMemo(() => buildDraftText(draft), [draft]);
  const gaps = useMemo(
    () =>
      [
        ['Source evidence', draft.source_evidence],
        ['Situation', draft.situation],
        ['Task', draft.task],
        ['Action', draft.action],
        ['Result', draft.result],
        ['Citations', draft.citations],
      ].filter(([, value]) => !String(value).trim()),
    [draft],
  );

  const saveAsset = useMutation({
    mutationFn: () =>
      apiFetch<ProofAsset>('/api/v1/proof/assets', {
        method: 'POST',
        body: JSON.stringify({
          title: draft.title,
          asset_type: draft.asset_type,
          status: coverage >= 90 ? 'ready' : 'draft',
          summary: draft.result,
          content_json: { ...draft, draft_text: draftText, planning_guidance_only: true },
          citations_json: draft.citations.split(';').map((item) => item.trim()).filter(Boolean),
          metadata_json: { target_role: draft.target_role, evidence_coverage: coverage },
        }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['proof-assets'] }),
  });

  const deleteAsset = useMutation({
    mutationFn: (id: string) => apiFetch(`/api/v1/proof/assets/${id}`, { method: 'DELETE' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['proof-assets'] }),
  });

  async function copyDraft() {
    await navigator.clipboard.writeText(draftText);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  if (!token) {
    return (
      <div className="space-y-6">
        <PageHeader eyebrow="Proof builder" title="Login to save proof assets" description="Proof assets are persisted behind authenticated user isolation." actions={<span className="pill border-amber-400/20 bg-amber-400/10 text-amber-100"><LockKeyhole className="h-3.5 w-3.5" /> Login required</span>} />
        <a href="/login" className="btn btn-primary">Login / Create Demo User</a>
      </div>
    );
  }

  const assets = assetsQuery.data || [];

  return (
    <div className="space-y-8">
      <PageHeader eyebrow="Proof builder" title="Turn evidence into persisted proof" description="Draft STAR stories, architecture notes, case studies, and posts while keeping missing evidence visible." actions={<span className="pill border-emerald-900 bg-emerald-950 text-emerald-300"><ShieldCheck className="h-3.5 w-3.5" /> No fabricated metrics</span>} />

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <MetricCard label="Evidence coverage" value={`${coverage}%`} detail="required fields completed" icon={Trophy} tone="text-emerald-300" />
        <MetricCard label="Open gaps" value={gaps.length} detail="fields still visible" icon={FileCheck2} tone={gaps.length ? 'text-amber-300' : 'text-emerald-300'} />
        <MetricCard label="Saved assets" value={assets.length} detail="backend persisted" icon={Save} tone="text-cyan-300" />
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="card">
          <SectionHeader title="Evidence form" description="Write from known source material, then save to your proof library." />
          <ProgressBar value={coverage} tone={coverage >= 90 ? 'bg-emerald-300' : 'bg-amber-300'} />
          <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="text-sm md:col-span-2"><span className="mb-2 block text-zinc-400">Title</span><input className="input" value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} /></label>
            <label className="text-sm"><span className="mb-2 block text-zinc-400">Asset type</span><select className="input" value={draft.asset_type} onChange={(event) => setDraft({ ...draft, asset_type: event.target.value })}>{ASSET_TYPES.map(([key, text]) => <option key={key} value={key}>{text}</option>)}</select></label>
            <label className="text-sm"><span className="mb-2 block text-zinc-400">Target role</span><input className="input" value={draft.target_role} onChange={(event) => setDraft({ ...draft, target_role: event.target.value })} /></label>
            {[
              ['source_evidence', 'Source evidence'],
              ['situation', 'Situation'],
              ['task', 'Task'],
              ['action', 'Action'],
              ['result', 'Result'],
              ['metric', 'Metric / proof'],
              ['citations', 'Citations'],
            ].map(([key, text]) => (
              <label key={key} className="text-sm md:col-span-2">
                <span className="mb-2 block text-zinc-400">{text}</span>
                <textarea className="input h-20" value={String(draft[key as keyof Draft])} onChange={(event) => setDraft({ ...draft, [key]: event.target.value })} />
              </label>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <section className="card">
            <SectionHeader title="Draft preview" description="Missing evidence remains explicit." action={<div className="flex gap-2"><button className="btn btn-secondary px-3 py-1.5" onClick={copyDraft}><Clipboard className="h-4 w-4" /> {copied ? 'Copied' : 'Copy'}</button><button className="btn btn-primary px-3 py-1.5" onClick={() => saveAsset.mutate()} disabled={saveAsset.isPending || !draft.title.trim()}><Save className="h-4 w-4" /> Save</button></div>} />
            <pre className="max-h-[520px] overflow-auto whitespace-pre-wrap rounded-lg border border-zinc-800 bg-zinc-950 p-4 text-sm leading-relaxed text-zinc-200">{draftText}</pre>
          </section>
          <section className="card">
            <SectionHeader title="Evidence gaps" description="Resolve these before treating the draft as ready." />
            {gaps.length ? <ul className="space-y-2 text-sm text-amber-300">{gaps.map(([gap]) => <li key={gap}>{gap}</li>)}</ul> : <EmptyState icon={CheckCircle2} title="Core evidence is present" description="The draft still needs human review, but required source fields are filled." />}
          </section>
        </div>
      </section>

      <section className="card">
        <SectionHeader title="Proof library" description="Saved records come from the authenticated backend, including approved campaign artifacts." />
        {assets.length ? (
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
            {assets.map((asset) => (
              <article key={asset.id} className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div><h3 className="font-medium text-white">{asset.title}</h3><p className="mt-1 text-xs text-zinc-500">{assetLabel(asset.asset_type)} | {asset.status}</p></div>
                  <button className="btn btn-secondary px-2 py-1" onClick={() => deleteAsset.mutate(asset.id)} aria-label={`Delete ${asset.title}`}><Trash2 className="h-3.5 w-3.5" /></button>
                </div>
                <p className="mt-3 line-clamp-4 text-sm text-zinc-400">{asset.summary || 'No summary yet.'}</p>
                <div className="mt-3 text-xs text-zinc-500">{new Date(asset.created_at).toLocaleDateString()}</div>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState icon={Trophy} title="No proof assets yet" description="Save a draft or approve a campaign artifact to build your library." />
        )}
      </section>
    </div>
  );
}
