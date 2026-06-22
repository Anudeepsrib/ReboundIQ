import Link from 'next/link';
import { ArrowRight, BriefcaseBusiness, FileText, Gauge, ShieldCheck, Trophy } from 'lucide-react';
import { PageHeader, SafetyNotice, SectionHeader } from '@/components/product-ui';

const steps = [
  {
    title: 'Model runway',
    detail: 'Add cash, severance, expenses, and contingency before planning outreach cadence.',
    href: '/runway',
    icon: Gauge,
  },
  {
    title: 'Upload resume',
    detail: 'Preserve the original, then create role-specific versions from source evidence.',
    href: '/resume',
    icon: FileText,
  },
  {
    title: 'Track target roles',
    detail: 'Move opportunities manually and keep each role tied to a JD snapshot.',
    href: '/applications',
    icon: BriefcaseBusiness,
  },
  {
    title: 'Build proof assets',
    detail: 'Create stories and narratives only from evidence you can cite.',
    href: '/proof',
    icon: Trophy,
  },
];

export default function Onboarding() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="First run"
        title="Set up the recovery workspace"
        description="Start with the deterministic planning tools, then add AI-assisted drafts only when source evidence is available."
        actions={
          <span className="pill border-emerald-400/20 bg-emerald-400/10 text-emerald-200">
            <ShieldCheck className="h-3.5 w-3.5" /> Local-first setup
          </span>
        }
      />

      <section className="card">
        <SectionHeader title="Recommended setup order" description="Each step maps to a working product route." />
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <Link key={step.href} href={step.href} className="interactive-card rounded-lg border border-white/10 bg-black/20 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex gap-3">
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-white/[0.04] text-xs font-semibold text-zinc-300">
                      {index + 1}
                    </span>
                    <div>
                      <Icon className="h-4 w-4 text-cyan-300" aria-hidden="true" />
                      <h2 className="mt-3 font-semibold text-white">{step.title}</h2>
                      <p className="mt-2 text-sm leading-6 text-zinc-400">{step.detail}</p>
                    </div>
                  </div>
                  <ArrowRight className="h-4 w-4 shrink-0 text-zinc-600" aria-hidden="true" />
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      <SafetyNotice tone="warning">
        Planning guidance only. Sensitive categories such as visa, finances, and health should be handled as risk signals, not advice.
      </SafetyNotice>
    </div>
  );
}
