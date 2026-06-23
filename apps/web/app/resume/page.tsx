'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, CheckCircle2, FileText, LockKeyhole, Upload, WandSparkles } from 'lucide-react';
import { apiFetch, getStoredToken } from '@/lib/api';

type ResumeUploadResult = {
  id: string;
  original_filename: string;
  created_at?: string;
  has_parsed?: boolean;
};

type ResumeVersionResult = {
  id: string;
  resume_id?: string;
  version_name: string;
  ats_score: number;
  content_json: Record<string, unknown>;
  source_inputs?: Record<string, unknown> | null;
  target_role?: string | null;
  created_at?: string;
};

export default function ResumePage() {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<ResumeUploadResult | null>(null);
  const [targetRole, setTargetRole] = useState('AI Engineer');
  const [version, setVersion] = useState<ResumeVersionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [token] = useState(() => getStoredToken());

  const resumesQuery = useQuery({
    queryKey: ['resumes'],
    queryFn: () => apiFetch<ResumeUploadResult[]>('/api/v1/resumes/'),
    enabled: Boolean(token),
  });

  const versionsQuery = useQuery({
    queryKey: ['resume-versions'],
    queryFn: () => apiFetch<ResumeVersionResult[]>('/api/v1/resumes/versions'),
    enabled: Boolean(token),
  });

  async function handleUpload() {
    if (!file) return;
    setLoading(true);
    setError('');
    const fd = new FormData();
    fd.append('file', file);
    try {
      const data = await apiFetch<ResumeUploadResult>('/api/v1/resumes/upload', { method: 'POST', body: fd });
      setUploadResult(data);
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Resume upload failed');
    } finally {
      setLoading(false);
    }
  }

  async function createVersion() {
    if (!uploadResult?.id) return;
    setLoading(true);
    setError('');
    const fd = new FormData();
    fd.append('target_role', targetRole);
    try {
      const data = await apiFetch<ResumeVersionResult>(`/api/v1/resumes/${uploadResult.id}/versions`, { method: 'POST', body: fd });
      setVersion(data);
      queryClient.invalidateQueries({ queryKey: ['resume-versions'] });
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Version create failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <header className="page-header">
        <div>
          <div className="eyebrow">Resume intelligence</div>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">Upload, preserve, tailor</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-400">
            Parsed resume records stay tied to the authenticated user. Role-specific versions never overwrite the original.
          </p>
        </div>
        <span className="pill border-emerald-400/20 bg-emerald-400/10 text-emerald-200">
          <LockKeyhole className="h-3.5 w-3.5" /> Originals preserved
        </span>
      </header>

      {!token && (
        <section className="card border-amber-400/20 bg-amber-400/10">
          <div className="flex items-start gap-3 text-sm text-amber-100">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <div className="font-semibold">Login required</div>
              <p className="mt-1 text-amber-100/80">Resume records are stored by authenticated user.</p>
              <a href="/login" className="btn btn-secondary mt-4 px-3 py-1.5">
                Login / Create Demo User
              </a>
            </div>
          </div>
        </section>
      )}

      {error && (
        <section className="rounded-lg border border-red-400/25 bg-red-500/10 p-4 text-sm text-red-100">
          {error}
        </section>
      )}

      <section className="grid grid-cols-1 gap-5 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="card">
          <div className="mb-5 flex items-center justify-between gap-3">
            <div>
              <h2 className="section-title">1. Upload source resume</h2>
              <p className="mt-1 text-xs text-zinc-500">PDF, DOCX, or TXT</p>
            </div>
            <Upload className="h-5 w-5 text-cyan-300" />
          </div>
          <input type="file" accept=".pdf,.docx,.txt" onChange={(event) => setFile(event.target.files?.[0] || null)} className="input" />
          <button onClick={handleUpload} disabled={!file || loading || !token} className="btn btn-primary mt-4 w-full sm:w-auto">
            <Upload className="h-4 w-4" /> {loading ? 'Working...' : 'Upload and parse'}
          </button>
          {uploadResult && (
            <div className="mt-4 rounded-lg border border-emerald-400/20 bg-emerald-400/10 p-3 text-sm text-emerald-100">
              <div className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
                <div>
                  <div className="font-medium">{uploadResult.original_filename}</div>
                  <div className="mt-1 break-all text-xs text-emerald-100/70">ID {uploadResult.id}</div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="card">
          <div className="mb-5 flex items-center justify-between gap-3">
            <div>
              <h2 className="section-title">2. Create a targeted version</h2>
              <p className="mt-1 text-xs text-zinc-500">Grounded suggestions only</p>
            </div>
            <WandSparkles className="h-5 w-5 text-emerald-300" />
          </div>
          <label className="block text-sm">
            <span className="mb-2 block text-zinc-400">Target role</span>
            <input value={targetRole} onChange={(event) => setTargetRole(event.target.value)} className="input" placeholder="AI Engineer" />
          </label>
          <button onClick={createVersion} disabled={loading || !token || !uploadResult} className="btn btn-secondary mt-4 w-full sm:w-auto">
            <FileText className="h-4 w-4" /> Create version
          </button>

          {!uploadResult && <div className="disclaimer mt-4">Upload a source resume before creating a tailored version.</div>}
        </div>
      </section>

      {version && (
        <section className="card">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="section-title">{version.version_name}</h2>
              <p className="mt-1 text-xs text-zinc-500">ATS score {version.ats_score}</p>
            </div>
            <span className="pill border-cyan-400/20 bg-cyan-400/10 text-cyan-200">Editable draft</span>
          </div>
          <pre className="scroll-panel max-h-[520px] overflow-auto whitespace-pre-wrap rounded-lg border border-white/10 bg-black/25 p-4 text-xs leading-relaxed text-zinc-300">
            {JSON.stringify(version.content_json, null, 2)}
          </pre>
          {version.source_inputs && (
            <div className="mt-3 rounded-lg border border-white/10 bg-black/20 p-3 text-xs leading-5 text-zinc-400">
              <div className="font-medium text-zinc-200">Grounding inputs</div>
              <pre className="mt-2 overflow-auto whitespace-pre-wrap">{JSON.stringify(version.source_inputs, null, 2)}</pre>
            </div>
          )}
          <div className="disclaimer mt-3">Source: your uploaded resume and stored grounding snippets. Edit before use.</div>
        </section>
      )}

      <section className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="card">
          <h2 className="section-title">Resume library</h2>
          <div className="mt-4 space-y-3">
            {(resumesQuery.data || []).map((resume) => (
              <article key={resume.id} className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 text-sm">
                <div className="font-medium text-white">{resume.original_filename}</div>
                <div className="mt-1 break-all text-xs text-zinc-500">{resume.id}</div>
                <button className="btn btn-secondary mt-3 px-3 py-1.5" onClick={() => setUploadResult(resume)}>
                  Use for new version
                </button>
              </article>
            ))}
            {!resumesQuery.data?.length && <div className="text-sm text-zinc-500">No uploaded resumes yet.</div>}
          </div>
        </div>

        <div className="card">
          <h2 className="section-title">Version history</h2>
          <div className="mt-4 space-y-3">
            {(versionsQuery.data || []).map((item) => (
              <article key={item.id} className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 text-sm">
                <div className="font-medium text-white">{item.version_name}</div>
                <div className="mt-1 text-xs text-zinc-500">{item.target_role || 'No target role'} | ATS {item.ats_score ?? 'n/a'}</div>
                {item.source_inputs && (
                  <div className="mt-2 text-xs text-zinc-500">
                    Grounded: {item.source_inputs.grounded ? 'yes' : 'review'} | Snippets {Number(item.source_inputs.recalled_snippets_count || 0)}
                  </div>
                )}
                <a
                  className="btn btn-secondary mt-3 px-3 py-1.5"
                  href={`/jobs?resumeVersionId=${encodeURIComponent(item.id)}${item.resume_id ? `&resumeId=${encodeURIComponent(item.resume_id)}` : ''}`}
                >
                  Use in JD match
                </a>
              </article>
            ))}
            {!versionsQuery.data?.length && <div className="text-sm text-zinc-500">No tailored versions yet.</div>}
          </div>
        </div>
      </section>

      <section className="card-subtle grid grid-cols-1 gap-3 text-sm text-zinc-400 md:grid-cols-3">
        <div>Original files are never overwritten.</div>
        <div>PII must pass redaction before any external provider.</div>
        <div>Claims need resume or knowledge-base citations.</div>
      </section>
    </div>
  );
}
