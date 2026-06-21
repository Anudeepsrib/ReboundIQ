'use client';

import React, { useMemo, useState } from 'react';
import { Calculator, CalendarDays, CircleDollarSign, Gauge, RotateCcw, ShieldAlert, WalletCards } from 'lucide-react';

type RunwayInputs = {
  cash: number;
  severance: number;
  monthlyIncome: number;
  housing: number;
  essentials: number;
  insurance: number;
  debtMinimums: number;
  oneTimeCosts: number;
  contingency: number;
};

type Scenario = {
  name: string;
  description: string;
  monthlyBurn: number;
  available: number;
  days: number;
};

const DEFAULT_INPUTS: RunwayInputs = {
  cash: 18000,
  severance: 9000,
  monthlyIncome: 1200,
  housing: 2400,
  essentials: 1300,
  insurance: 650,
  debtMinimums: 450,
  oneTimeCosts: 1800,
  contingency: 900,
};

const currency = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

function money(value: number) {
  return currency.format(Math.round(value || 0));
}

function clampNumber(value: number) {
  if (Number.isNaN(value)) return 0;
  return Math.max(0, value);
}

function riskForDays(days: number) {
  if (days < 45) return { label: 'Critical', className: 'text-red-300', border: 'border-red-900 bg-red-950/40' };
  if (days < 90) return { label: 'Tight', className: 'text-amber-300', border: 'border-amber-900 bg-amber-950/40' };
  if (days < 150) return { label: 'Monitor', className: 'text-cyan-300', border: 'border-cyan-900 bg-cyan-950/40' };
  return { label: 'Stable', className: 'text-emerald-300', border: 'border-emerald-900 bg-emerald-950/40' };
}

function runwayDays(available: number, monthlyBurn: number) {
  if (monthlyBurn <= 0) return 365;
  return Math.max(0, Math.round((available / monthlyBurn) * 30.4375));
}

export default function RunwayPlanner() {
  const [inputs, setInputs] = useState<RunwayInputs>(DEFAULT_INPUTS);

  function updateInput(key: keyof RunwayInputs, value: string) {
    setInputs((current) => ({ ...current, [key]: clampNumber(Number(value)) }));
  }

  const model = useMemo(() => {
    const monthlyExpenses = inputs.housing + inputs.essentials + inputs.insurance + inputs.debtMinimums + inputs.contingency;
    const baseMonthlyBurn = Math.max(0, monthlyExpenses - inputs.monthlyIncome);
    const baseAvailable = Math.max(0, inputs.cash + inputs.severance - inputs.oneTimeCosts);
    const scenarios: Scenario[] = [
      {
        name: 'Conservative',
        description: 'Higher burn and lower available buffer',
        monthlyBurn: baseMonthlyBurn * 1.15,
        available: baseAvailable * 0.95,
        days: runwayDays(baseAvailable * 0.95, baseMonthlyBurn * 1.15),
      },
      {
        name: 'Moderate',
        description: 'Current planned expenses',
        monthlyBurn: baseMonthlyBurn,
        available: baseAvailable,
        days: runwayDays(baseAvailable, baseMonthlyBurn),
      },
      {
        name: 'Lean',
        description: 'Reduced discretionary burn',
        monthlyBurn: baseMonthlyBurn * 0.85,
        available: baseAvailable,
        days: runwayDays(baseAvailable, baseMonthlyBurn * 0.85),
      },
    ];

    const moderate = scenarios[1];
    const actionItems = [
      'Validate severance dates, benefits windows, and recurring obligations against source documents.',
      moderate.days < 90
        ? 'Bias the weekly plan toward active interviews, warm referrals, and roles with clear match evidence.'
        : 'Maintain a balanced weekly plan across resume tailoring, targeted applications, proof assets, and interview practice.',
      inputs.debtMinimums > 0
        ? 'Track minimum obligations separately from discretionary spend before changing repayment behavior.'
        : 'Keep a separate buffer for expenses that do not appear every month.',
      inputs.insurance > 0
        ? 'Review benefits and coverage deadlines with official plan documents or a qualified professional.'
        : 'Add any benefits, coverage, or transition costs before relying on this estimate.',
    ];

    return {
      monthlyExpenses,
      baseMonthlyBurn,
      baseAvailable,
      scenarios,
      actionItems,
      risk: riskForDays(moderate.days),
    };
  }, [inputs]);

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Runway Planner</h1>
          <p className="mt-1 text-sm text-zinc-400">Cash runway, burn-rate scenarios, and weekly risk signals.</p>
        </div>
        <span className={`pill ${model.risk.border}`}>
          <Gauge className="h-3.5 w-3.5" />
          <span className={model.risk.className}>{model.risk.label} risk</span>
        </span>
      </header>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="card">
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            <WalletCards className="h-4 w-4 text-emerald-300" /> Available buffer
          </div>
          <div className="metric mt-3">{money(model.baseAvailable)}</div>
          <div className="mt-2 text-xs text-zinc-500">Cash plus severance minus one-time transition costs.</div>
        </div>
        <div className="card">
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            <CircleDollarSign className="h-4 w-4 text-amber-300" /> Monthly burn
          </div>
          <div className="metric mt-3">{money(model.baseMonthlyBurn)}</div>
          <div className="mt-2 text-xs text-zinc-500">Expenses and contingency after expected monthly income.</div>
        </div>
        <div className="card">
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            <CalendarDays className="h-4 w-4 text-cyan-300" /> Moderate runway
          </div>
          <div className="metric mt-3">{model.scenarios[1].days} days</div>
          <div className="mt-2 text-xs text-zinc-500">{Math.round(model.scenarios[1].days / 30.4375)} months at current inputs.</div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="card">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="section-title">Inputs</h2>
            <button className="btn btn-secondary px-3 py-1.5" onClick={() => setInputs(DEFAULT_INPUTS)}>
              <RotateCcw className="h-4 w-4" /> Reset
            </button>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {[
              ['cash', 'Cash on hand'],
              ['severance', 'Severance / payouts'],
              ['monthlyIncome', 'Monthly transition income'],
              ['housing', 'Housing'],
              ['essentials', 'Essentials'],
              ['insurance', 'Benefits / insurance'],
              ['debtMinimums', 'Debt minimums'],
              ['oneTimeCosts', 'One-time transition costs'],
              ['contingency', 'Monthly contingency'],
            ].map(([key, label]) => (
              <label key={key} className="text-sm">
                <span className="mb-2 block text-zinc-400">{label}</span>
                <input
                  className="input"
                  type="number"
                  min={0}
                  step={50}
                  value={inputs[key as keyof RunwayInputs]}
                  onChange={(event) => updateInput(key as keyof RunwayInputs, event.target.value)}
                />
              </label>
            ))}
          </div>
        </div>

        <div className="card">
          <h2 className="section-title">Action checklist</h2>
          <ul className="mt-4 space-y-3 text-sm text-zinc-300">
            {model.actionItems.map((item) => (
              <li key={item} className="flex gap-3">
                <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" aria-hidden="true" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
          <div className="disclaimer mt-5">
            Planning guidance and risk signals only. Not financial, legal, immigration, tax, or medical advice.
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {model.scenarios.map((scenario) => {
          const risk = riskForDays(scenario.days);
          return (
            <article key={scenario.name} className={`card ${risk.border}`}>
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="font-medium text-white">{scenario.name}</h2>
                  <p className="mt-1 text-xs text-zinc-400">{scenario.description}</p>
                </div>
                <Calculator className="h-5 w-5 text-zinc-400" aria-hidden="true" />
              </div>
              <div className="mt-5 text-4xl font-semibold tracking-tight text-white">{scenario.days}</div>
              <div className="mt-1 text-sm text-zinc-400">days runway</div>
              <dl className="mt-5 space-y-2 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-zinc-500">Available</dt>
                  <dd>{money(scenario.available)}</dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-zinc-500">Monthly burn</dt>
                  <dd>{money(scenario.monthlyBurn)}</dd>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <dt className="text-zinc-500">Signal</dt>
                  <dd className={risk.className}>{risk.label}</dd>
                </div>
              </dl>
            </article>
          );
        })}
      </section>
    </div>
  );
}
