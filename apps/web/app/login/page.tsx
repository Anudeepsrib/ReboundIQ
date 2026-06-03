'use client';
import React, { useState } from 'react';
export default function Login() {
  const [email, setEmail] = useState('demo@reboundiq.local');
  const [msg, setMsg] = useState('');
  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  async function doLogin() {
    const r = await fetch(`${API}/api/v1/auth/login`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({email, password: 'demo'}) });
    const d = await r.json();
    localStorage.setItem('token', d.access_token);
    setMsg('Logged in (demo). Go to Dashboard.');
  }
  return (
    <div className="max-w-sm mx-auto card">
      <h1 className="text-xl mb-4">Login (Demo)</h1>
      <input className="input mb-2" value={email} onChange={e=>setEmail(e.target.value)} />
      <button onClick={doLogin} className="btn btn-primary w-full">Login (any email works in slice)</button>
      {msg && <div className="mt-2 text-emerald-400 text-sm">{msg}</div>}
      <div className="text-xs mt-4">In prod: real JWT + password or SSO.</div>
    </div>
  );
}
