'use client';

import React, { useState } from 'react';

export default function ResumePage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [targetRole, setTargetRole] = useState('AI Engineer');
  const [version, setVersion] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  async function handleUpload() {
    if (!file) return;
    setLoading(true);
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(`${API}/api/v1/resumes/upload`, { method: 'POST', body: fd });
    const data = await res.json();
    setUploadResult(data);
    setLoading(false);
  }

  async function createVersion() {
    if (!uploadResult?.id) return;
    setLoading(true);
    const fd = new FormData();
    fd.append('target_role', targetRole);
    const res = await fetch(`${API}/api/v1/resumes/${uploadResult.id}/versions`, { method: 'POST', body: fd });
    const data = await res.json();
    setVersion(data);
    setLoading(false);
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-semibold mb-2">Resume Intelligence</h1>
      <p className="text-zinc-400 mb-6">Upload PDF/DOCX/TXT. Parsed + structured. Generate role-specific versions (never overwrites original). All grounded in your data.</p>

      <div className="card mb-6">
        <div className="mb-3 text-sm">1. Upload resume</div>
        <input type="file" accept=".pdf,.docx,.txt" onChange={e => setFile(e.target.files?.[0] || null)} className="input mb-3" />
        <button onClick={handleUpload} disabled={!file || loading} className="btn btn-primary">Upload &amp; Parse (local AI)</button>
        {uploadResult && <div className="mt-3 text-xs text-emerald-400">Uploaded: {uploadResult.original_filename} • ID {uploadResult.id}</div>}
      </div>

      {uploadResult && (
        <div className="card mb-6">
          <div className="mb-3 text-sm">2. Generate targeted version</div>
          <input value={targetRole} onChange={e=>setTargetRole(e.target.value)} className="input mb-3" placeholder="Target role e.g. AI Engineer" />
          <button onClick={createVersion} disabled={loading} className="btn btn-secondary">Create {targetRole} Version (AI rewrite suggestions)</button>

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
