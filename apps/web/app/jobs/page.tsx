'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, CirclePlus, FileSearch, Gauge, ListChecks, ShieldCheck, Sparkles } from 'lucide-react';
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

type Resume = {
  id: string;
  original_filename: string;
};

type ResumeVersion = {
  id: string;
  resume_id?: string;
  version_name: string;
  target_role?: string | null;
};

function pct(value?: number) {
  return Math.round((value || 0) * 100);
}

export default function JobsAnalyzer() {
  const queryClient = useQueryClient();
  const [jd, setJd] = useState('');
  const [resumeText, setResumeText] = useState('');
  const [resumeId, setResumeId] = useState('');
  const [resumeVersionId, setResumeVersionId] = useState('');
  const [company, setCompany] = useState('');
  const [role, setRole] = useState('');
  const [result, setResult] = useState<MatchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [token] = useState(() => getStoredToken());

  const resumesQuery = useQuery({
    queryKey: ['resumes'],
    queryFn: () => apiFetch<Resume[]>('/api/v1/resumes/'),
    enabled: Boolean(token),
  });

  const versionsQuery = useQuery({
    queryKey: ['resume-versions'],
    queryFn: () => apiFetch<ResumeVersion[]>('/api/v1/resumes/versions'),
    enabled: Boolean(token),
  });

  async function analyze() {
    if (!jd.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = await apiFetch<MatchResult>('/api/v1/jobs/analyze', {
        method: 'POST',
        body: JSON.stringify({
          jd_text: jd,
          resume_text: resumeText || undefined,
          resume_id: resumeId || undefined,
          resume_version_id: resumeVersionId || undefined,
        }),
      });
      setResult(data);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'JD analysis failed');
    } finally {
      setLoading(false);
    }
  }

  const saveApplication = useMutation({
    mutationFn: () =>
      apiFetch('/api/v1/applications', {
        method: 'POST',
        body: JSON.stringify({
          company: company.trim() || 'Unknown company',
          role: role.trim() || 'Target role',
          status: 'saved',
          jd_snapshot: jd.slice(0, 12000),
          notes: result?.rewrite_strategy || 'Created from JD match analysis.',
          next_step: 'Review evidence fit and decide whether to apply.',
          fit_score: result?.match_score || 0,
          resume_version_id: resumeVersionId || null,
          sponsorship_signal: result?.red_flags?.join('; ') || 'unknown',
          metadata_json: {
            source: 'jd_analysis',
            citations: result?.citations || [],
            groundedness_score: result?.groundedness_score || 0,
          },
        }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['applications'] }),
  });

  return (
    <div className="space-y-8">
      <header className="page-header">
        <div>
          <div className="eyebrow">JD match</div>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">Evidence-based role fit</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-400">
            Extract required skills, compare against supplied evidence, and keep missing evidence visible.
          </p>
        </div>
        <span className="pill border-emerald-400/20 bg-emerald-400/10 text-emerald-200">
          <ShieldCheck className="h-3.5 w-3.5" /> Grounded output
        </span>
      </header>

      {!token && (
        <section className="card border-amber-400/20 bg-amber-400/10">
          <div className="flex items-start gap-3 text-sm text-amber-100">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <div className="font-semibold">Login required</div>
              <p className="mt-1 text-amber-100/80">Authenticated analysis keeps job and resume records isolated by user.</p>
              <a href="/login" className="btn btn-secondary mt-4 px-3 py-1.5">
                Login / Create Demo User
              </a>
            </div>
          </div>
        </section>
      )}

      <section className="grid grid-cols-1 gap-5 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="card">
          <div className="mb-5 flex items-center justify-between gap-3">
            <h2 className="section-title">Role evidence</h2>
            <FileSearch className="h-5 w-5 text-cyan-300" />
          </div>
          <label className="block text-sm">
            <span className="mb-2 block text-zinc-400">Job description</span>
            <textarea
              value={jd}
              onChange={(event) => setJd(event.target.value)}
              placeholder="Paste full job description here..."
              className="input h-56 font-mono text-xs leading-5"
            />
          </label>
          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="text-sm">
              <span className="mb-2 block text-zinc-400">Company</span>
              <input value={company} onChange={(event) => setCompany(event.target.value)} className="input" placeholder="Company name" />
            </label>
            <label className="text-sm">
              <span className="mb-2 block text-zinc-400">Role</span>
              <input value={role} onChange={(event) => setRole(event.target.value)} className="input" placeholder="Target role" />
            </label>
          </div>
          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="text-sm">
              <span className="mb-2 block text-zinc-400">Stored resume</span>
              <select className="input" value={resumeId} onChange={(event) => { setResumeId(event.target.value); setResumeVersionId(''); }}>
                <option value="">No stored resume selected</option>
                {(resumesQuery.data || []).map((resume) => <option key={resume.id} value={resume.id}>{resume.original_filename}</option>)}
              </select>
            </label>
            <label className="text-sm">
              <span className="mb-2 block text-zinc-400">Resume version</span>
              <select className="input" value={resumeVersionId} onChange={(event) => setResumeVersionId(event.target.value)}>
                <option value="">No version selected</option>
                {(versionsQuery.data || [])
                  .filter((version) => !resumeId || version.resume_id === resumeId)
                  .map((version) => <option key={version.id} value={version.id}>{version.version_name}</option>)}
              </select>
            </label>
          </div>
          <label className="mt-4 block text-sm">
            <span className="mb-2 block text-zinc-400">Resume or profile excerpt</span>
            <textarea
              value={resumeText}
              onChange={(event) => setResumeText(event.target.value)}
              placeholder="Optional evidence for stronger groundedness..."
              className="input h-32 font-mono text-xs leading-5"
            />
          </label>
          <button onClick={analyze} disabled={loading || !jd.trim() || !token} className="btn btn-primary mt-5">
            <Sparkles className="h-4 w-4" /> {loading ? 'Analyzing...' : 'Analyze JD'}
          </button>
          {!resumeId && !resumeVersionId && !resumeText.trim() && (
            <div className="mt-3 text-xs text-amber-300">No resume evidence selected. Analysis will extract JD requirements but will not infer personal fit.</div>
          )}
          {error && <div className="mt-4 rounded-lg border border-red-400/25 bg-red-500/10 p-3 text-sm text-red-100">{error}</div>}
        </div>

        <aside className="space-y-4">
          <section className="card">
            <div className="muted-label">Output contract</div>
            <ul className="mt-4 space-y-3 text-sm text-zinc-300">
              <li className="flex gap-2">
                <ListChecks className="mt-0.5 h-4 w-4 text-emerald-300" /> Required and missing skills stay separate.
              </li>
              <li className="flex gap-2">
                <ShieldCheck className="mt-0.5 h-4 w-4 text-cyan-300" /> Personal claims need citations.
              </li>
              <li className="flex gap-2">
                <AlertTriangle className="mt-0.5 h-4 w-4 text-amber-300" /> Drafts require human review before use.
              </li>
            </ul>
          </section>
          <section className="card">
            <div className="text-sm text-zinc-400">Current input length</div>
            <div className="mt-3 grid grid-cols-2 gap-3">
              <div className="stat-card">
                <div className="metric text-lg">{jd.trim().length}</div>
                <div className="mt-1 text-xs text-zinc-500">JD chars</div>
              </div>
              <div className="stat-card">
                <div className="metric text-lg">{resumeText.trim().length}</div>
                <div className="mt-1 text-xs text-zinc-500">Profile chars</div>
              </div>
            </div>
          </section>
        </aside>
      </section>

      {result && (
        <section className="grid grid-cols-1 gap-5 lg:grid-cols-[0.95fr_1.05fr]">
          <div className="card">
            <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="section-title">Match score</h2>
                <div className="mt-3 text-5xl font-semibold tracking-tight text-white">{result.match_score}</div>
              </div>
              <span className="pill border-cyan-400/20 bg-cyan-400/10 text-cyan-200">/100</span>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="stat-card">
                <div className="flex items-center gap-2 text-xs text-zinc-400">
                  <Gauge className="h-3.5 w-3.5" /> AI confidence
                </div>
                <div className="mt-2 text-2xl font-semibold text-white">{pct(result.ai_confidence)}%</div>
              </div>
              <div className="stat-card">
                <div className="flex items-center gap-2 text-xs text-zinc-400">
                  <ShieldCheck className="h-3.5 w-3.5" /> Groundedness
                </div>
                <div className="mt-2 text-2xl font-semibold text-white">{pct(result.groundedness_score)}%</div>
              </div>
            </div>
            {result.warnings?.[0] && <div className="mt-4 text-xs text-amber-300">{result.warnings[0]}</div>}

            <dl className="mt-5 space-y-3 text-sm">
              <div>
                <dt className="text-zinc-500">Required</dt>
                <dd className="mt-1 text-zinc-200">{result.required_skills?.join(', ') || 'None extracted'}</dd>
              </div>
              <div>
                <dt className="text-zinc-500">Missing evidence</dt>
                <dd className="mt-1 text-zinc-200">{result.missing_skills?.join(', ') || 'None extracted'}</dd>
              </div>
              <div>
                <dt className="text-zinc-500">Red flags</dt>
                <dd className="mt-1 text-zinc-200">{result.red_flags?.join(' | ') || 'None extracted'}</dd>
              </div>
              <div>
                <dt className="text-zinc-500">Citations</dt>
                <dd className="mt-1 text-zinc-200">{result.citations?.join('; ') || 'No citations returned'}</dd>
              </div>
            </dl>
            <div className="mt-5 text-xs text-zinc-500">
              Citations {result.quality?.citation_count || 0} | Required skills {result.quality?.required_skill_count || 0} | Missing{' '}
              {result.quality?.missing_skill_count || 0}
            </div>
          </div>

          <div className="card text-sm">
            <h2 className="section-title">Rewrite strategy</h2>
            <div className="mt-3 whitespace-pre-wrap leading-6 text-zinc-300">{result.rewrite_strategy}</div>
            <h2 className="section-title mt-6">Recruiter message draft</h2>
            <div className="mt-3 whitespace-pre-wrap rounded-lg border border-white/10 bg-black/25 p-4 text-xs leading-5 text-zinc-300">
              {result.recruiter_message_draft || 'No recruiter draft generated because resume evidence is missing.'}
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button className="btn btn-primary" onClick={() => saveApplication.mutate()} disabled={saveApplication.isPending || !result}>
                <CirclePlus className="h-4 w-4" /> {saveApplication.isPending ? 'Saving...' : 'Save as application'}
              </button>
              <a href="/applications" className="btn btn-secondary">Open pipeline</a>
            </div>
            <div className="disclaimer mt-3">Edit heavily. Do not send fabricated claims.</div>
          </div>
        </section>
      )}
    </div>
  );
}
