'use client';

import { useState } from 'react';
import { KeyRound, LockKeyhole, ShieldCheck, UserPlus } from 'lucide-react';
import { API_BASE, setStoredTokens } from '@/lib/api';
import { PageHeader, SafetyNotice, SectionHeader } from '@/components/product-ui';

type TokenResponse = {
  access_token?: string;
  refresh_token?: string;
  detail?: string;
};

export default function Login() {
  const [email, setEmail] = useState('demo@reboundiq.local');
  const [password, setPassword] = useState('demo-password');
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(false);

  async function doLogin() {
    setLoading(true);
    setMsg('');
    try {
      let response = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (response.status === 401 || response.status === 422) {
        response = await fetch(`${API_BASE}/api/v1/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, full_name: 'Demo User' }),
        });
      }
      const data = (await response.json()) as TokenResponse;
      if (!response.ok || !data.access_token) {
        throw new Error(data.detail || 'Login failed');
      }
      setStoredTokens(data.access_token, data.refresh_token);
      setMsg('Logged in. Campaigns and JD Match can now call the authenticated API.');
    } catch (error) {
      setMsg(error instanceof Error ? error.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <PageHeader
        eyebrow="Demo access"
        title="Authenticate local workflows"
        description="Use the demo credentials to create or reuse a JWT-backed account for user-isolated API calls."
        actions={
          <span className="pill border-emerald-400/20 bg-emerald-400/10 text-emerald-200">
            <ShieldCheck className="h-3.5 w-3.5" /> User scoped
          </span>
        }
      />

      <section className="grid grid-cols-1 gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="card">
          <SectionHeader title="Login or create demo user" description="Registration is automatic when the demo user does not exist yet." />
          <label className="block text-sm">
            <span className="mb-2 block text-zinc-400">Email</span>
            <input className="input" value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          <label className="mt-4 block text-sm">
            <span className="mb-2 block text-zinc-400">Password</span>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={8}
            />
          </label>
          <button onClick={doLogin} className="btn btn-primary mt-5 w-full" disabled={loading || password.length < 8}>
            <KeyRound className="h-4 w-4" /> {loading ? 'Signing in...' : 'Login / Create Demo User'}
          </button>
          {msg && (
            <div className="mt-4 rounded-lg border border-emerald-400/20 bg-emerald-400/10 p-3 text-sm text-emerald-100">
              {msg}
            </div>
          )}
        </div>

        <aside className="space-y-4">
          <div className="card">
            <SectionHeader title="What authentication unlocks" description="These workflows require backend user isolation." />
            <div className="space-y-3 text-sm text-zinc-300">
              <div className="flex gap-3 rounded-lg border border-white/10 bg-black/20 p-3">
                <UserPlus className="mt-0.5 h-4 w-4 text-cyan-300" />
                <span>Resume uploads, JD analysis, and campaigns are tied to the authenticated user.</span>
              </div>
              <div className="flex gap-3 rounded-lg border border-white/10 bg-black/20 p-3">
                <LockKeyhole className="mt-0.5 h-4 w-4 text-amber-300" />
                <span>Campaign records, approval queues, and AI events stay behind JWT-backed requests.</span>
              </div>
            </div>
          </div>
          <SafetyNotice>
            In production, this surface can be replaced with SSO or managed credentials while preserving the same API boundary.
          </SafetyNotice>
        </aside>
      </section>
    </div>
  );
}
