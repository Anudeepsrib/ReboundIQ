'use client';

import React, { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CalendarDays, CircleDollarSign, Gauge, LockKeyhole, Save, Trash2, WalletCards } from 'lucide-react';
import { apiFetch, getStoredToken } from '@/lib/api';
import { EmptyState, MetricCard, PageHeader, ProgressBar, SafetyNotice, SectionHeader } from '@/components/product-ui';

type RunwaySnapshot = {
  id: string;
  title: string;
  scenario: string;
  risk_level: string;
  monthly_expenses: number;
  savings_balance: number;
  severance_amount: number;
  unemployment_amount: number;
  target_months: number;
  assumptions_json?: Record<string, unknown> | null;
  action_items_json?: Array<string | Record<string, unknown>> | null;
  disclaimer_acknowledged: boolean;
  created_at: string;
};

const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });

function money(value: number) {
  return currency.format(Math.round(value || 0));
}

function riskForMonths(months: number) {
  if (months < 1.5) return { label: 'critical', className: 'text-red-300', tone: 'bg-red-300' };
  if (months < 3) return { label: 'tight', className: 'text-amber-300', tone: 'bg-amber-300' };
  if (months < 5) return { label: 'monitor', className: 'text-cyan-300', tone: 'bg-cyan-300' };
  return { label: 'stable', className: 'text-emerald-300', tone: 'bg-emerald-300' };
}

export default function RunwayPlanner() {
  const queryClient = useQueryClient();
  const [token] = useState(() => getStoredToken());
  const [title, setTitle] = useState('Current runway');
  const [cash, setCash] = useState(18000);
  const [severance, setSeverance] = useState(9000);
  const [unemployment, setUnemployment] = useState(1200);
  const [monthlyExpenses, setMonthlyExpenses] = useState(5700);
  const [targetMonths, setTargetMonths] = useState(6);

  const snapshotsQuery = useQuery({
    queryKey: ['runway-snapshots'],
    queryFn: () => apiFetch<RunwaySnapshot[]>('/api/v1/runway/snapshots'),
    enabled: Boolean(token),
  });

  const model = useMemo(() => {
    const available = Math.max(0, cash + severance);
    const burn = Math.max(0, monthlyExpenses - unemployment);
    const months = burn > 0 ? available / burn : targetMonths;
    const risk = riskForMonths(months);
    return {
      available,
      burn,
      months,
      days: Math.round(months * 30.4375),
      risk,
      actions: [
        'Validate severance, benefits, and recurring obligations against source documents.',
        months < 3 ? 'Prioritize warm referrals and roles with strong evidence fit this week.' : 'Balance applications, proof assets, and interview practice across the week.',
        'Keep legal, immigration, tax, financial, and benefits questions with qualified professionals.',
      ],
    };
  }, [cash, severance, monthlyExpenses, targetMonths, unemployment]);

  const saveSnapshot = useMutation({
    mutationFn: () =>
      apiFetch<RunwaySnapshot>('/api/v1/runway/snapshots', {
        method: 'POST',
        body: JSON.stringify({
          title,
          scenario: 'base',
          risk_level: model.risk.label,
          monthly_expenses: monthlyExpenses,
          savings_balance: cash,
          severance_amount: severance,
          unemployment_amount: unemployment,
          target_months: targetMonths,
          assumptions_json: { modeled_months: Number(model.months.toFixed(2)), modeled_days: model.days },
          action_items_json: model.actions,
          disclaimer_acknowledged: true,
        }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['runway-snapshots'] }),
  });

  const deleteSnapshot = useMutation({
    mutationFn: (id: string) => apiFetch(`/api/v1/runway/snapshots/${id}`, { method: 'DELETE' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['runway-snapshots'] }),
  });

  if (!token) {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Runway planner"
          title="Login to save runway snapshots"
          description="Runway data is user-scoped and persisted only after authentication."
          actions={<span className="pill border-amber-400/20 bg-amber-400/10 text-amber-100"><LockKeyhole className="h-3.5 w-3.5" /> Login required</span>}
        />
        <a href="/login" className="btn btn-primary">Login / Create Demo User</a>
      </div>
    );
  }

  const snapshots = snapshotsQuery.data || [];

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Runway planner"
        title="Model and save your transition window"
        description="Persist conservative runway snapshots with planning disclaimers and weekly action signals."
        actions={<span className={`pill border-zinc-800 bg-zinc-950 ${model.risk.className}`}><Gauge className="h-3.5 w-3.5" /> {model.risk.label}</span>}
      />

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <MetricCard label="Available buffer" value={money(model.available)} detail="Cash plus severance." icon={WalletCards} tone="text-emerald-300" />
        <MetricCard label="Monthly burn" value={money(model.burn)} detail="Expenses after transition income." icon={CircleDollarSign} tone="text-amber-300" />
        <MetricCard label="Modeled runway" value={`${model.days} days`} detail={`${model.months.toFixed(1)} months at current inputs.`} icon={CalendarDays} tone="text-cyan-300" />
      </section>

      <section className="card-subtle">
        <ProgressBar value={(model.months / targetMonths) * 100} tone={model.risk.tone} label={`${targetMonths}-month target`} />
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="card">
          <SectionHeader title="Snapshot inputs" description="Use conservative values and save each material change." />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="text-sm md:col-span-2">
              <span className="mb-2 block text-zinc-400">Title</span>
              <input className="input" value={title} onChange={(event) => setTitle(event.target.value)} />
            </label>
            {[
              ['Cash on hand', cash, setCash],
              ['Severance / payouts', severance, setSeverance],
              ['Monthly transition income', unemployment, setUnemployment],
              ['Monthly expenses', monthlyExpenses, setMonthlyExpenses],
              ['Target months', targetMonths, setTargetMonths],
            ].map(([label, value, setter]) => (
              <label key={String(label)} className="text-sm">
                <span className="mb-2 block text-zinc-400">{String(label)}</span>
                <input
                  className="input"
                  type="number"
                  min={0}
                  value={Number(value)}
                  onChange={(event) => (setter as React.Dispatch<React.SetStateAction<number>>)(Number(event.target.value))}
                />
              </label>
            ))}
          </div>
          <button className="btn btn-primary mt-5" onClick={() => saveSnapshot.mutate()} disabled={saveSnapshot.isPending || !title.trim()}>
            <Save className="h-4 w-4" /> {saveSnapshot.isPending ? 'Saving...' : 'Save snapshot'}
          </button>
          <SafetyNotice tone="warning">Planning guidance and risk signals only. Not financial, legal, immigration, tax, or medical advice.</SafetyNotice>
        </div>

        <div className="card">
          <SectionHeader title="Saved snapshots" description="Backend-persisted and scoped to your authenticated user." />
          {snapshots.length ? (
            <div className="space-y-3">
              {snapshots.map((snapshot) => {
                const available = snapshot.savings_balance + snapshot.severance_amount;
                const burn = Math.max(0, snapshot.monthly_expenses - snapshot.unemployment_amount);
                const months = burn > 0 ? available / burn : snapshot.target_months;
                const risk = riskForMonths(months);
                return (
                  <article key={snapshot.id} className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <h2 className="font-medium text-white">{snapshot.title}</h2>
                        <p className="mt-1 text-xs text-zinc-500">{new Date(snapshot.created_at).toLocaleDateString()}</p>
                      </div>
                      <span className={`pill border-zinc-800 bg-zinc-900 ${risk.className}`}>{risk.label}</span>
                    </div>
                    <dl className="mt-4 grid grid-cols-3 gap-3 text-sm">
                      <div><dt className="text-xs text-zinc-500">Buffer</dt><dd>{money(available)}</dd></div>
                      <div><dt className="text-xs text-zinc-500">Burn</dt><dd>{money(burn)}</dd></div>
                      <div><dt className="text-xs text-zinc-500">Months</dt><dd>{months.toFixed(1)}</dd></div>
                    </dl>
                    <button className="btn btn-secondary mt-4 px-3 py-1.5" onClick={() => deleteSnapshot.mutate(snapshot.id)}>
                      <Trash2 className="h-4 w-4" /> Delete
                    </button>
                  </article>
                );
              })}
            </div>
          ) : (
            <EmptyState icon={CalendarDays} title="No snapshots saved" description="Save the current model to create your first persisted runway record." />
          )}
        </div>
      </section>
    </div>
  );
}
