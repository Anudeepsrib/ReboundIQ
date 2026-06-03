'use client';

import React from 'react';
import Link from 'next/link';

export default function Dashboard() {
  return (
    <div>
      <div className="mb-8">
        <div className="flex items-end justify-between">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">Layoff Recovery Dashboard</h1>
            <p className="text-zinc-400 mt-1">Demo user • Local AI (Ollama) • External disabled • All data private to you</p>
          </div>
          <div className="text-xs px-3 py-1 rounded-full border border-emerald-900 bg-emerald-950 text-emerald-400">30-day runway: 82 days (moderate)</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="card">
          <div className="text-sm text-zinc-400">Layoff-to-Offer Progress</div>
          <div className="mt-3 h-2 bg-zinc-800 rounded"><div className="h-2 w-[42%] bg-emerald-500 rounded" /></div>
          <div className="mt-2 text-xs">Resume 78% • Applications 3/12 • Interview ready 35%</div>
        </div>
        <div className="card">
          <div className="text-sm text-zinc-400">Risk Signals</div>
          <ul className="mt-2 text-sm space-y-1">
            <li className="text-emerald-400">✓ Runway: moderate (82d)</li>
            <li className="text-amber-400">⚠ Resume: 1 tailored version ready</li>
            <li className="text-red-400">✗ Portfolio: 0 proof assets</li>
            <li>Visa sensitivity: H-1B (planning only)</li>
          </ul>
        </div>
        <div className="card">
          <div className="text-sm text-zinc-400">AI Provider</div>
          <div className="mt-2 text-lg font-medium">Ollama • llama3.2:1b (local)</div>
          <div className="text-emerald-400 text-xs mt-1">External AI: DISABLED (no consent)</div>
          <Link href="/settings/ai-providers" className="text-xs underline mt-2 inline-block">Configure providers →</Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card">
          <h3 className="font-medium mb-3">Quick Actions</h3>
          <div className="flex flex-wrap gap-2">
            <Link href="/resume" className="btn btn-primary">Upload / Analyze Resume</Link>
            <Link href="/jobs" className="btn btn-secondary">Paste JD &amp; Match</Link>
            <Link href="/campaigns" className="btn btn-secondary">Start Campaign (Deep Agent)</Link>
          </div>
          <div className="disclaimer mt-4">All generated content is editable. Source data and citations shown. Never overwrite originals.</div>
        </div>

        <div className="card">
          <h3 className="font-medium mb-3">This Week&apos;s Plan (stub)</h3>
          <ul className="text-sm space-y-2">
            <li>1. Update resume for AI Engineer role (use JD match output)</li>
            <li>2. Generate 2 proof assets from past project (evidence only)</li>
            <li>3. 5 targeted outreach drafts (manual send)</li>
            <li>4. 1 mock interview session</li>
            <li>5. Track 3 applications in pipeline</li>
          </ul>
          <div className="text-[10px] text-amber-400 mt-3">This is planning guidance, not advice. Adjust to your real constraints.</div>
        </div>
      </div>

      <div className="mt-8 text-xs text-zinc-500">
        ReboundIQ v0.1 vertical slice • See design in .design/ for full 23-PR plan • Local-first, consent-first, grounded, no fabrication.
      </div>
    </div>
  );
}
