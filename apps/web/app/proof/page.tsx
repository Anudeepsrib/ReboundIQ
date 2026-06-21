'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, Clipboard, FileCheck2, Save, ShieldCheck, Trash2, Trophy } from 'lucide-react';

const ASSET_TYPES = ['STAR story', 'Architecture narrative', 'GitHub README', 'LinkedIn post'] as const;

type AssetType = (typeof ASSET_TYPES)[number];

type ProofDraft = {
  title: string;
  assetType: AssetType;
  targetRole: string;
  sourceEvidence: string;
  situation: string;
  task: string;
  action: string;
  result: string;
  metric: string;
  citations: string;
};

type SavedAsset = {
  id: string;
  title: string;
  assetType: AssetType;
  targetRole: string;
  coverage: number;
  createdAt: string;
};

const STORAGE_KEY = 'reboundiq.proof-assets.v1';

const DEFAULT_DRAFT: ProofDraft = {
  title: 'Privacy-first AI gateway rollout',
  assetType: 'Architecture narrative',
  targetRole: 'Senior AI Platform Engineer',
  sourceEvidence: 'Design doc, gateway implementation notes, eval results, audit log schema.',
  situation: 'The product needed AI-assisted career workflows without exposing personal data by default.',
  task: 'Design a provider-neutral path where local Ollama remained the default and external providers required consent.',
  action:
    'Introduced a single AI gateway, routed generation through redaction and compliance checks, and kept deterministic services authoritative.',
  result: 'The system could support resume and JD workflows while preserving user isolation, auditability, and manual approval.',
  metric: '',
  citations: 'README local-first policy; AGENTS.md non-negotiables; ai_requests schema.',
};

function parseSavedAssets(raw: string | null) {
  if (!raw) return [] as SavedAsset[];

  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((asset): asset is SavedAsset => {
      return (
        typeof asset?.id === 'string' &&
        typeof asset.title === 'string' &&
        ASSET_TYPES.includes(asset.assetType) &&
        typeof asset.coverage === 'number'
      );
    });
  } catch {
    return [];
  }
}

function coverageForDraft(draft: ProofDraft) {
  const fields: Array<keyof ProofDraft> = [
    'title',
    'targetRole',
    'sourceEvidence',
    'situation',
    'task',
    'action',
    'result',
    'citations',
  ];
  const completed = fields.filter((field) => draft[field].trim().length > 0).length;
  return Math.round((completed / fields.length) * 100);
}

function buildDraftText(draft: ProofDraft) {
  const metric = draft.metric.trim() || 'Metric not provided; keep this claim qualitative until evidence exists.';

  if (draft.assetType === 'STAR story') {
    return `Title: ${draft.title}
Target role: ${draft.targetRole}

Situation: ${draft.situation || 'Situation evidence missing.'}
Task: ${draft.task || 'Task evidence missing.'}
Action: ${draft.action || 'Action evidence missing.'}
Result: ${draft.result || 'Result evidence missing.'}
Metric / proof: ${metric}

Citations: ${draft.citations || 'Citations missing.'}`;
  }

  if (draft.assetType === 'GitHub README') {
    return `# ${draft.title || 'Proof Asset'}

## Problem
${draft.situation || 'Problem evidence missing.'}

## My Contribution
${draft.action || 'Contribution evidence missing.'}

## Result
${draft.result || 'Result evidence missing.'}

## Evidence
${draft.sourceEvidence || 'Evidence sources missing.'}

## Boundaries
${metric}

## Citations
${draft.citations || 'Citations missing.'}`;
  }

  if (draft.assetType === 'LinkedIn post') {
    return `${draft.title}

I worked on a problem where ${draft.situation || '[situation evidence missing]'}

My role was to ${draft.task || '[task evidence missing]'}.

The useful part was the design tradeoff: ${draft.action || '[action evidence missing]'}

Outcome: ${draft.result || '[result evidence missing]'}

Evidence I can point to: ${draft.sourceEvidence || '[evidence missing]'}

${metric}`;
  }

  return `${draft.title || 'Architecture narrative'}

Context
${draft.situation || 'Context evidence missing.'}

Responsibility
${draft.task || 'Responsibility evidence missing.'}

Architecture / decision
${draft.action || 'Architecture decision evidence missing.'}

Outcome
${draft.result || 'Outcome evidence missing.'}

Evidence
${draft.sourceEvidence || 'Evidence sources missing.'}

Measurement
${metric}

Citations
${draft.citations || 'Citations missing.'}`;
}

export default function ProofBuilder() {
  const [draft, setDraft] = useState<ProofDraft>(DEFAULT_DRAFT);
  const [savedAssets, setSavedAssets] = useState<SavedAsset[]>([]);
  const [isHydrated, setIsHydrated] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setSavedAssets(parseSavedAssets(window.localStorage.getItem(STORAGE_KEY)));
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (!isHydrated) return;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(savedAssets));
  }, [savedAssets, isHydrated]);

  const draftText = useMemo(() => buildDraftText(draft), [draft]);
  const coverage = useMemo(() => coverageForDraft(draft), [draft]);
  const gaps = useMemo(() => {
    const checks = [
      ['Source evidence', draft.sourceEvidence],
      ['Situation', draft.situation],
      ['Task', draft.task],
      ['Action', draft.action],
      ['Result', draft.result],
      ['Citations', draft.citations],
    ];
    return checks.filter(([, value]) => !value.trim()).map(([label]) => label);
  }, [draft]);

  async function copyDraft() {
    await navigator.clipboard.writeText(draftText);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  }

  function saveAsset() {
    if (!draft.title.trim()) return;

    setSavedAssets((current) => [
      {
        id: `proof-${Date.now()}`,
        title: draft.title.trim(),
        assetType: draft.assetType,
        targetRole: draft.targetRole,
        coverage,
        createdAt: new Date().toISOString().slice(0, 10),
      },
      ...current,
    ]);
  }

  function deleteAsset(id: string) {
    setSavedAssets((current) => current.filter((asset) => asset.id !== id));
  }

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Proof-of-Work Builder</h1>
          <p className="mt-1 text-sm text-zinc-400">STAR stories, case studies, READMEs, and posts grounded in supplied evidence.</p>
        </div>
        <span className="pill border-emerald-900 bg-emerald-950 text-emerald-300">
          <ShieldCheck className="h-3.5 w-3.5" /> No fabricated metrics
        </span>
      </header>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="card">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="section-title">Evidence form</h2>
            <span className="pill border-zinc-800 bg-zinc-950 text-zinc-300">
              <Trophy className="h-3.5 w-3.5" /> {coverage}% coverage
            </span>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="text-sm md:col-span-2">
              <span className="mb-2 block text-zinc-400">Title</span>
              <input className="input" value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} />
            </label>
            <label className="text-sm">
              <span className="mb-2 block text-zinc-400">Asset type</span>
              <select
                className="input"
                value={draft.assetType}
                onChange={(event) => setDraft({ ...draft, assetType: event.target.value as AssetType })}
              >
                {ASSET_TYPES.map((type) => (
                  <option key={type}>{type}</option>
                ))}
              </select>
            </label>
            <label className="text-sm">
              <span className="mb-2 block text-zinc-400">Target role</span>
              <input className="input" value={draft.targetRole} onChange={(event) => setDraft({ ...draft, targetRole: event.target.value })} />
            </label>
            <label className="text-sm md:col-span-2">
              <span className="mb-2 block text-zinc-400">Source evidence</span>
              <textarea
                className="input h-20"
                value={draft.sourceEvidence}
                onChange={(event) => setDraft({ ...draft, sourceEvidence: event.target.value })}
              />
            </label>
            {[
              ['situation', 'Situation'],
              ['task', 'Task'],
              ['action', 'Action'],
              ['result', 'Result'],
              ['metric', 'Metric / proof'],
              ['citations', 'Citations'],
            ].map(([key, label]) => (
              <label key={key} className="text-sm md:col-span-2">
                <span className="mb-2 block text-zinc-400">{label}</span>
                <textarea
                  className="input h-20"
                  value={draft[key as keyof ProofDraft]}
                  onChange={(event) => setDraft({ ...draft, [key]: event.target.value })}
                />
              </label>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <section className="card">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <h2 className="section-title">Draft preview</h2>
              <div className="flex flex-wrap gap-2">
                <button className="btn btn-secondary px-3 py-1.5" onClick={copyDraft}>
                  <Clipboard className="h-4 w-4" /> {copied ? 'Copied' : 'Copy'}
                </button>
                <button className="btn btn-primary px-3 py-1.5" onClick={saveAsset} disabled={!draft.title.trim()}>
                  <Save className="h-4 w-4" /> Save
                </button>
              </div>
            </div>
            <pre className="max-h-[520px] overflow-auto whitespace-pre-wrap rounded-lg border border-zinc-800 bg-zinc-950 p-4 text-sm leading-relaxed text-zinc-200">
              {draftText}
            </pre>
            <div className="disclaimer mt-3">Review before use. Any missing evidence remains visible instead of being inferred.</div>
          </section>

          <section className="card">
            <h2 className="section-title">Evidence gaps</h2>
            {gaps.length ? (
              <ul className="mt-4 space-y-2 text-sm text-amber-300">
                {gaps.map((gap) => (
                  <li key={gap} className="flex items-center gap-2">
                    <FileCheck2 className="h-4 w-4" aria-hidden="true" /> {gap}
                  </li>
                ))}
              </ul>
            ) : (
              <div className="mt-4 flex items-center gap-2 text-sm text-emerald-300">
                <CheckCircle2 className="h-4 w-4" /> Core evidence fields are present.
              </div>
            )}
          </section>
        </div>
      </section>

      <section className="card">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="section-title">Local proof board</h2>
          <span className="text-xs text-zinc-500">{savedAssets.length} saved</span>
        </div>
        {savedAssets.length ? (
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
            {savedAssets.map((asset) => (
              <article key={asset.id} className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="font-medium text-white">{asset.title}</h3>
                    <p className="mt-1 text-xs text-zinc-500">{asset.assetType} for {asset.targetRole}</p>
                  </div>
                  <button className="btn btn-secondary px-2 py-1" onClick={() => deleteAsset(asset.id)} aria-label={`Delete ${asset.title}`}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
                <div className="mt-4 h-1.5 rounded bg-zinc-800">
                  <div className="h-1.5 rounded bg-emerald-500" style={{ width: `${asset.coverage}%` }} />
                </div>
                <div className="mt-2 text-xs text-zinc-400">{asset.coverage}% evidence coverage • {asset.createdAt}</div>
              </article>
            ))}
          </div>
        ) : (
          <p className="text-sm text-zinc-400">Saved proof assets stay in this browser for the demo slice.</p>
        )}
      </section>
    </div>
  );
}
