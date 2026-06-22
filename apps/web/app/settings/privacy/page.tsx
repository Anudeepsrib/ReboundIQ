'use client';

import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Archive, Database, FileDown, LockKeyhole, ShieldCheck, Trash2 } from 'lucide-react';
import { apiFetch, clearStoredTokens, getStoredToken } from '@/lib/api';
import { MetricCard, PageHeader, SafetyNotice, SectionHeader } from '@/components/product-ui';

type UserMe = {
  id: string;
  email: string;
  full_name?: string | null;
  role: string;
  consents: Record<string, boolean>;
};

type DeleteResult = {
  ok: boolean;
  deleted_rows: Record<string, number>;
  deleted_files: number;
};

function downloadJson(filename: string, value: unknown) {
  const blob = new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export default function Privacy() {
  const [token] = useState(() => getStoredToken());
  const [confirmation, setConfirmation] = useState('');
  const [exportMessage, setExportMessage] = useState('');
  const [deleteResult, setDeleteResult] = useState<DeleteResult | null>(null);

  const meQuery = useQuery({
    queryKey: ['me'],
    queryFn: () => apiFetch<UserMe>('/api/v1/auth/me'),
    enabled: Boolean(token),
  });

  const exportMutation = useMutation({
    mutationFn: () => apiFetch<Record<string, unknown>>('/api/v1/privacy/export'),
    onSuccess: (data) => {
      downloadJson(`reboundiq-export-${new Date().toISOString().slice(0, 10)}.json`, data);
      setExportMessage('Export generated and downloaded as JSON.');
    },
    onError: (error) => setExportMessage(error instanceof Error ? error.message : 'Export failed'),
  });

  const deleteMutation = useMutation({
    mutationFn: () =>
      apiFetch<DeleteResult>('/api/v1/privacy/delete-account', {
        method: 'POST',
        body: JSON.stringify({ confirmation }),
      }),
    onSuccess: (data) => {
      setDeleteResult(data);
      clearStoredTokens();
    },
  });

  if (!token) {
    return (
      <div className="space-y-6">
        <PageHeader eyebrow="Privacy controls" title="Login to manage your data" description="Export, consent, and delete controls require an authenticated user." actions={<span className="pill border-amber-400/20 bg-amber-400/10 text-amber-100"><LockKeyhole className="h-3.5 w-3.5" /> Login required</span>} />
        <a href="/login" className="btn btn-primary">Login / Create Demo User</a>
      </div>
    );
  }

  const consents = meQuery.data?.consents || {};

  return (
    <div className="space-y-8">
      <PageHeader eyebrow="Privacy controls" title="Data stays user-scoped" description="Export, consent status, hard delete, and audit surfaces are backed by authenticated API calls." actions={<span className="pill border-emerald-400/20 bg-emerald-400/10 text-emerald-200"><ShieldCheck className="h-3.5 w-3.5" /> Privacy-first</span>} />

      <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <MetricCard label="AI default" value="Local" detail="Ollama provider path" icon={Database} tone="text-emerald-300" />
        <MetricCard label="External AI" value={consents.external_ai ? 'Consented' : 'Disabled'} detail="per-user consent" icon={ShieldCheck} tone={consents.external_ai ? 'text-amber-300' : 'text-emerald-300'} />
        <MetricCard label="Sensitive memory" value={consents.memory_sensitive ? 'Allowed' : 'Blocked'} detail="requires explicit consent" icon={LockKeyhole} tone="text-amber-300" />
        <MetricCard label="Visa mode" value={consents.visa_processing ? 'Allowed' : 'Blocked'} detail="planning guidance only" icon={Archive} tone="text-cyan-300" />
      </section>

      <section className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_1fr]">
        <div className="card">
          <SectionHeader title="Export all data" description="Downloads structured records and readable stored files as base64 JSON when storage permits." />
          <button className="btn btn-primary" onClick={() => exportMutation.mutate()} disabled={exportMutation.isPending}>
            <FileDown className="h-4 w-4" /> {exportMutation.isPending ? 'Exporting...' : 'Download export'}
          </button>
          {exportMessage && <div className="mt-4 rounded-lg border border-white/10 bg-black/20 p-3 text-sm text-zinc-300">{exportMessage}</div>}
        </div>

        <div className="card border-red-400/25">
          <SectionHeader title="Hard delete account" description="Deletes user-owned database rows and the user storage prefix. This cannot be undone." />
          <label className="block text-sm">
            <span className="mb-2 block text-zinc-400">Type DELETE to confirm</span>
            <input className="input" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} />
          </label>
          <button className="btn btn-secondary mt-4" onClick={() => deleteMutation.mutate()} disabled={deleteMutation.isPending || confirmation !== 'DELETE'}>
            <Trash2 className="h-4 w-4" /> {deleteMutation.isPending ? 'Deleting...' : 'Delete account'}
          </button>
          {deleteMutation.error && <SafetyNotice tone="danger">{deleteMutation.error instanceof Error ? deleteMutation.error.message : 'Delete failed'}</SafetyNotice>}
          {deleteResult && <SafetyNotice tone="warning">Account deleted. Rows removed: {Object.values(deleteResult.deleted_rows).reduce((sum, value) => sum + value, 0)}. Files removed: {deleteResult.deleted_files}. Please log in again to continue.</SafetyNotice>}
        </div>
      </section>

      <section className="card">
        <SectionHeader title="Audit surfaces" description="AI and deterministic user actions are exported and deleted through the same user-owned boundary." />
        <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
          {['ai_requests', 'agent_tool_calls', 'action_audit_logs', 'memory_*'].map((table) => (
            <code key={table} className="rounded-lg border border-white/10 bg-black/20 p-3 text-center text-xs text-zinc-300">{table}</code>
          ))}
        </div>
      </section>
    </div>
  );
}
