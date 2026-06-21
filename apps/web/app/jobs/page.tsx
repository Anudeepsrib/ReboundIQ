'use client';

import React, { useState } from 'react';

type MatchResult = {
  match_score: number;
  required_skills?: string[];
  missing_skills?: string[];
  red_flags?: string[];
  citations?: string[];
  warnings?: string[];
  rewrite_strategy?: string;
  recruiter_message_draft?: string;
};

export default function JobsAnalyzer() {
  const [jd, setJd] = useState('');
  const [result, setResult] = useState<MatchResult | null>(null);
  const [loading, setLoading] = useState(false);

  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  async function analyze() {
    if (!jd.trim()) return;
    setLoading(true);
    const res = await fetch(`${API}/api/v1/jobs/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jd_text: jd })
    });
    const data = (await res.json()) as MatchResult;
    setResult(data);
    setLoading(false);
  }

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-semibold mb-2">Job Description Analyzer + Match</h1>
      <p className="text-zinc-400 mb-4">Paste JD. Evidence-based extraction + match against your profile (upload resume first for better results in full). Match score, missing skills, rewrite strategy, drafts — all with citations and warnings. No guarantees.</p>

      <textarea value={jd} onChange={e=>setJd(e.target.value)} placeholder="Paste full job description here..." className="input h-48 font-mono text-xs mb-3" />
      <button onClick={analyze} disabled={loading || !jd.trim()} className="btn btn-primary">Analyze JD &amp; Generate Match (local AI)</button>

      {result && (
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="card">
            <div className="font-medium mb-2">Match Score: {result.match_score}/100</div>
            <div className="text-xs mb-3 warning">{result.warnings?.[0]}</div>
            <div><strong>Required:</strong> {result.required_skills?.join(', ')}</div>
            <div className="mt-1"><strong>Missing (evidence-based):</strong> {result.missing_skills?.join(', ')}</div>
            <div className="mt-1"><strong>Red flags:</strong> {result.red_flags?.join(' | ') || 'None extracted'}</div>
            <div className="mt-1"><strong>Citations:</strong> {result.citations?.join('; ')}</div>
          </div>
          <div className="card text-sm">
            <div className="font-medium">Rewrite Strategy</div>
            <div className="mt-1 whitespace-pre-wrap">{result.rewrite_strategy}</div>
            <div className="mt-4 font-medium">Recruiter Message Draft</div>
            <div className="mt-1 p-2 bg-black/40 rounded text-xs">{result.recruiter_message_draft}</div>
            <div className="mt-3 text-[10px] text-zinc-500">Edit heavily. This is a starting point grounded in the JD + your data. Do not send fabricated claims.</div>
          </div>
        </div>
      )}
    </div>
  );
}
