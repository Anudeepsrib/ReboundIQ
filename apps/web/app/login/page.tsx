'use client';
import React, { useState } from 'react';
import { API_BASE, setStoredTokens } from '@/lib/api';

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
    <div className="max-w-sm mx-auto card">
      <h1 className="text-xl mb-4">Login (Demo)</h1>
      <input className="input mb-2" value={email} onChange={(event) => setEmail(event.target.value)} />
      <input
        className="input mb-3"
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        minLength={8}
      />
      <button onClick={doLogin} className="btn btn-primary w-full" disabled={loading || password.length < 8}>
        {loading ? 'Signing in...' : 'Login / Create Demo User'}
      </button>
      {msg && <div className="mt-2 text-sm text-emerald-400">{msg}</div>}
      <div className="text-xs mt-4 text-zinc-500">In prod: SSO or managed credentials with the same JWT-backed API.</div>
    </div>
  );
}
