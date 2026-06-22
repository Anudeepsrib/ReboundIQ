import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';

function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(' ');
}

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
}) {
  return (
    <header className="page-header">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">{title}</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-400">{description}</p>
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </header>
  );
}

export function SectionHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h2 className="section-title">{title}</h2>
        {description && <p className="mt-1 text-xs leading-5 text-zinc-500">{description}</p>}
      </div>
      {action}
    </div>
  );
}

export function MetricCard({
  label,
  value,
  detail,
  icon: Icon,
  tone = 'text-white',
}: {
  label: string;
  value: ReactNode;
  detail?: string;
  icon?: LucideIcon;
  tone?: string;
}) {
  return (
    <article className="card">
      <div className="flex items-center justify-between gap-3">
        <div className="text-sm text-zinc-400">{label}</div>
        {Icon && <Icon className={cx('h-4 w-4', tone)} aria-hidden="true" />}
      </div>
      <div className={cx('metric mt-3', tone)}>{value}</div>
      {detail && <div className="mt-2 text-xs leading-5 text-zinc-500">{detail}</div>}
    </article>
  );
}

export function ProgressBar({
  value,
  tone = 'bg-emerald-300',
  label,
}: {
  value: number;
  tone?: string;
  label?: string;
}) {
  const width = Math.max(0, Math.min(100, Math.round(value)));
  return (
    <div>
      {label && (
        <div className="mb-2 flex items-center justify-between gap-3 text-xs">
          <span className="text-zinc-500">{label}</span>
          <span className="font-semibold text-zinc-200">{width}%</span>
        </div>
      )}
      <div className="progress-track">
        <div className={cx('h-full rounded-full', tone)} style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-lg border border-dashed border-white/15 bg-black/20 p-6 text-center">
      <Icon className="mx-auto h-6 w-6 text-zinc-500" aria-hidden="true" />
      <h3 className="mt-4 font-semibold text-white">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-zinc-500">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function SafetyNotice({
  children,
  tone = 'neutral',
}: {
  children: ReactNode;
  tone?: 'neutral' | 'success' | 'warning' | 'danger';
}) {
  const tones = {
    neutral: 'border-white/10 bg-white/[0.04] text-zinc-300',
    success: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-100',
    warning: 'border-amber-400/20 bg-amber-400/10 text-amber-100',
    danger: 'border-red-400/25 bg-red-500/10 text-red-100',
  };

  return <div className={cx('rounded-lg border p-4 text-sm leading-6', tones[tone])}>{children}</div>;
}
