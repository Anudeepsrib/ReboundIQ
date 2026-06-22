'use client';

import React, { useState } from 'react';
import { apiFetch, getStoredToken } from '@/lib/api';

type ResumeUploadResult = {
  id: string;
  original_filename: string;
};

type ResumeVersionResult = {
  version_name: string;
  ats_score: number;
  content_json: Record<string, unknown>;
};

export default function ResumePage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<ResumeUploadResult | null>(null);
  const [targetRole, setTargetRole] = useState('AI Engineer');
  const [version, setVersion] = useState<ResumeVersionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [token] = useState(() => getStoredToken());

  async function handleUpload() {
    if (!file) return;
    setLoading(true);
    setError('');
    const fd = new FormData();
    fd.append('file', file);
    try {
      const data = await apiFetch<ResumeUploadResult>('/api/v1/resumes/upload', { method: 'POST', body: fd });
      setUploadResult(data);
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
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Version create failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-semibold mb-2">Resume Intelligence</h1>
      <p className="text-zinc-400 mb-6">Upload PDF/DOCX/TXT. Parsed + structured. Generate role-specific versions (never overwrites original). All grounded in your data.</p>
      {!token && (
        <div className="mb-4 rounded-lg border border-amber-900 bg-amber-950/30 p-3 text-sm text-amber-200">
          Login is required because resume records are stored by authenticated user.
          <a href="/login" className="btn btn-secondary mt-3 px-3 py-1.5">Login / Create Demo User</a>
        </div>
      )}
      {error && <div className="mb-4 text-sm text-red-300">{error}</div>}

      <div className="card mb-6">
        <div className="mb-3 text-sm">1. Upload resume</div>
        <input type="file" accept=".pdf,.docx,.txt" onChange={e => setFile(e.target.files?.[0] || null)} className="input mb-3" />
        <button onClick={handleUpload} disabled={!file || loading || !token} className="btn btn-primary">Upload &amp; Parse (local AI)</button>
        {uploadResult && <div className="mt-3 text-xs text-emerald-400">Uploaded: {uploadResult.original_filename} • ID {uploadResult.id}</div>}
      </div>

      {uploadResult && (
        <div className="card mb-6">
          <div className="mb-3 text-sm">2. Generate targeted version</div>
          <input value={targetRole} onChange={e=>setTargetRole(e.target.value)} className="input mb-3" placeholder="Target role e.g. AI Engineer" />
          <button onClick={createVersion} disabled={loading || !token} className="btn btn-secondary">Create {targetRole} Version (AI rewrite suggestions)</button>

          {version && (
            <div className="mt-4 p-4 bg-zinc-950 border border-zinc-800 rounded">
              <div className="font-medium">{version.version_name}</div>
              <div className="text-xs text-zinc-400">ATS score: {version.ats_score} (demo)</div>
              <pre className="text-xs mt-3 whitespace-pre-wrap text-zinc-300">{JSON.stringify(version.content_json, null, 2)}</pre>
              <div className="disclaimer">Source: your uploaded resume. Edit before use. Citations would appear here in full RAG version.</div>
            </div>
          )}
        </div>
      )}

      <div className="text-xs text-zinc-500">In full build: side-by-side compare, version history, ATS breakdown, export MD/PDF, RAG citations from your KB, never store PII in prompts without redaction.</div>
    </div>
  );
}
