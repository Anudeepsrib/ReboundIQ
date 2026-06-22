'use client';

import React, { useState } from 'react';
import { AlertTriangle, Gauge, ShieldCheck } from 'lucide-react';
import { apiFetch, getStoredToken } from '@/lib/api';

type MatchResult = {
  match_score: number;
  ai_confidence?: number;
  groundedness_score?: number;
  quality?: {
    citation_count?: number;
    required_skill_count?: number;
    missing_skill_count?: number;
    user_resume_supplied?: boolean;
    scoring_note?: string;
  };
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
  const [resumeText, setResumeText] = useState('');
  const [result, setResult] = useState<MatchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [token] = useState(() => getStoredToken());

  async function analyze() {
    if (!jd.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = await apiFetch<MatchResult>('/api/v1/jobs/analyze', {
        method: 'POST',
        body: JSON.stringify({ jd_text: jd, resume_text: resumeText || undefined }),
      });
      setResult(data);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'JD analysis failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-semibold mb-2">Job Description Analyzer + Match</h1>
      <p className="text-zinc-400 mb-4">Paste JD. Evidence-based extraction + match against your profile. No guarantees.</p>

      {!token && (
        <div className="mb-4 rounded-lg border border-amber-900 bg-amber-950/30 p-3 text-sm text-amber-200">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" /> Login required for authenticated match analysis.
          </div>
          <a href="/login" className="btn btn-secondary mt-3 px-3 py-1.5">
            Login / Create Demo User
          </a>
        </div>
      )}

      <textarea value={jd} onChange={e=>setJd(e.target.value)} placeholder="Paste full job description here..." className="input h-48 font-mono text-xs mb-3" />
      <textarea
        value={resumeText}
        onChange={(event) => setResumeText(event.target.value)}
        placeholder="Optional resume/profile excerpt for stronger groundedness..."
        className="input mb-3 h-28 font-mono text-xs"
      />
      <button onClick={analyze} disabled={loading || !jd.trim() || !token} className="btn btn-primary">
        Analyze JD &amp; Generate Match (local AI)
      </button>
      {error && <div className="mt-3 text-sm text-red-300">{error}</div>}

      {result && (
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="card">
            <div className="font-medium mb-2">Match Score: {result.match_score}/100</div>
            <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                <div className="flex items-center gap-2 text-xs text-zinc-400">
                  <Gauge className="h-3.5 w-3.5" /> AI confidence
                </div>
                <div className="mt-2 text-xl font-semibold text-white">{Math.round((result.ai_confidence || 0) * 100)}%</div>
              </div>
              <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                <div className="flex items-center gap-2 text-xs text-zinc-400">
                  <ShieldCheck className="h-3.5 w-3.5" /> Groundedness
                </div>
                <div className="mt-2 text-xl font-semibold text-white">{Math.round((result.groundedness_score || 0) * 100)}%</div>
              </div>
            </div>
            <div className="text-xs mb-3 warning">{result.warnings?.[0]}</div>
            <div><strong>Required:</strong> {result.required_skills?.join(', ')}</div>
            <div className="mt-1"><strong>Missing (evidence-based):</strong> {result.missing_skills?.join(', ')}</div>
            <div className="mt-1"><strong>Red flags:</strong> {result.red_flags?.join(' | ') || 'None extracted'}</div>
            <div className="mt-1"><strong>Citations:</strong> {result.citations?.join('; ')}</div>
            <div className="mt-3 text-xs text-zinc-500">
              Citations: {result.quality?.citation_count || 0} • Required skills: {result.quality?.required_skill_count || 0} • Missing skills:{' '}
              {result.quality?.missing_skill_count || 0}
            </div>
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
