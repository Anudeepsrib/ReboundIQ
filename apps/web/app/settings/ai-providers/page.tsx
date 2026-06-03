'use client';

import React, { useEffect, useState } from 'react';

export default function AIProviders() {
  const [status, setStatus] = useState<any>(null);
  const [consentText, setConsentText] = useState('I understand external AI may send (redacted) data and this is optional. I consent.');
  const [enable, setEnable] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  async function load() {
    const r = await fetch(`${API}/api/v1/ai/status`);
    setStatus(await r.json());
  }
  useEffect(() => { load(); }, []);

  async function toggleExternal() {
    const r = await fetch(`${API}/api/v1/ai/consent/external-ai`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ enable_external: enable, consent_text: consentText })
    });
    const d = await r.json();
    alert(JSON.stringify(d));
    load();
  }

  async function test() {
    const r = await fetch(`${API}/api/v1/ai/test`, { method: 'POST' });
    setTestResult(await r.json());
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-semibold mb-4">AI Provider Settings</h1>

      <div className="card mb-6">
        <div className="text-sm mb-2">Current Status (from backend)</div>
        <pre className="text-xs bg-black p-3 rounded">{JSON.stringify(status, null, 2)}</pre>
        <button onClick={load} className="btn btn-secondary mt-2">Refresh</button>
      </div>

      <div className="card">
        <div className="font-medium mb-2">External AI Consent (disabled by default)</div>
        <div className="text-xs text-amber-400 mb-2">Enabling sends (redacted) data to third-party. Local Ollama recommended and sufficient for most workflows.</div>
        <label className="flex items-center gap-2 text-sm mb-2">
          <input type="checkbox" checked={enable} onChange={e=>setEnable(e.target.checked)} /> Enable external providers (after consent)
        </label>
        <textarea value={consentText} onChange={e=>setConsentText(e.target.value)} className="input h-20 text-xs mb-2" />
        <button onClick={toggleExternal} className="btn btn-primary">Record Consent &amp; Update</button>

        <div className="mt-4">
          <button onClick={test} className="btn btn-secondary">Test current provider connection</button>
          {testResult && <pre className="text-xs mt-2">{JSON.stringify(testResult)}</pre>}
        </div>
        <div className="disclaimer">PII redaction runs before any external call. All calls audited. You can revoke anytime.</div>
      </div>
    </div>
  );
}
