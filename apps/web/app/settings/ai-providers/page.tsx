'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Bot, CheckCircle2, Cpu, PlugZap, RefreshCcw, Save, ShieldCheck, TriangleAlert } from 'lucide-react';
import { EmptyState, MetricCard, PageHeader, ProgressBar, SectionHeader, SafetyNotice } from '@/components/product-ui';

type ProviderStatus = {
  provider: string;
  chat_model: string;
  embedding_model: string;
  local_base_url: string;
  external_enabled: boolean;
  local_available: boolean;
  local_models: string[];
  chat_model_present: boolean;
  embedding_model_present: boolean;
  redaction_enabled: boolean;
  memory_provider: string;
};

type LocalModelsResponse = {
  provider: string;
  base_url: string;
  chat_model: string;
  embedding_model: string;
  installed_models: string[];
  suggested_models: string[];
  warning: string;
};

type ActionResult = {
  ok?: boolean;
  error?: string;
  warning?: string;
  provider?: string;
  chat_model?: string;
  embedding_model?: string;
  chat_model_present?: boolean;
  sample?: string;
};

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const FALLBACK_STATUS: ProviderStatus = {
  provider: 'ollama',
  chat_model: 'llama3.2:1b',
  embedding_model: 'nomic-embed-text',
  local_base_url: 'http://localhost:11434',
  external_enabled: false,
  local_available: false,
  local_models: [],
  chat_model_present: false,
  embedding_model_present: false,
  redaction_enabled: true,
  memory_provider: 'unknown',
};

const FALLBACK_MODEL_INFO: LocalModelsResponse = {
  provider: 'ollama',
  base_url: 'http://localhost:11434',
  chat_model: 'llama3.2:1b',
  embedding_model: 'nomic-embed-text',
  installed_models: [],
  suggested_models: ['llama3.2:1b', 'llama3.2:3b', 'gemma3:4b', 'gemma2:9b', 'mistral:7b', 'qwen2.5:7b', 'phi3:mini'],
  warning: 'API is not reachable yet.',
};

function uniqueModels(values: string[]) {
  return Array.from(new Set(values.filter(Boolean))).sort((a, b) => a.localeCompare(b));
}

export default function AIProviders() {
  const [status, setStatus] = useState<ProviderStatus | null>(null);
  const [modelInfo, setModelInfo] = useState<LocalModelsResponse | null>(null);
  const [chatModel, setChatModel] = useState('llama3.2:1b');
  const [embeddingModel, setEmbeddingModel] = useState('nomic-embed-text');
  const [baseUrl, setBaseUrl] = useState('http://localhost:11434');
  const [customModel, setCustomModel] = useState('');
  const [consentText, setConsentText] = useState('I understand external AI may send (redacted) data and this is optional. I consent.');
  const [enable, setEnable] = useState(false);
  const [testResult, setTestResult] = useState<ActionResult | null>(null);
  const [saveResult, setSaveResult] = useState<ActionResult | null>(null);
  const [loading, setLoading] = useState(false);

  const selectableModels = useMemo(() => {
    return uniqueModels([
      ...(modelInfo?.installed_models || []),
      ...(modelInfo?.suggested_models || []),
      chatModel,
      'custom',
    ]);
  }, [chatModel, modelInfo]);

  async function load() {
    try {
      const [statusResponse, localModelsResponse] = await Promise.all([
        fetch(`${API}/api/v1/ai/status`),
        fetch(`${API}/api/v1/ai/local-models`),
      ]);
      if (!statusResponse.ok || !localModelsResponse.ok) {
        throw new Error('AI settings API is not ready');
      }
      const nextStatus = (await statusResponse.json()) as ProviderStatus;
      const nextModelInfo = (await localModelsResponse.json()) as LocalModelsResponse;
      setStatus(nextStatus);
      setModelInfo(nextModelInfo);
      setChatModel(nextStatus.chat_model);
      setEmbeddingModel(nextStatus.embedding_model);
      setBaseUrl(nextStatus.local_base_url);
      setEnable(nextStatus.external_enabled);
      setSaveResult(null);
    } catch (error) {
      setStatus(FALLBACK_STATUS);
      setModelInfo(FALLBACK_MODEL_INFO);
      setChatModel(FALLBACK_STATUS.chat_model);
      setEmbeddingModel(FALLBACK_STATUS.embedding_model);
      setBaseUrl(FALLBACK_STATUS.local_base_url);
      setEnable(false);
      setSaveResult({ ok: false, error: error instanceof Error ? error.message : 'AI settings API is not reachable' });
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function saveLocalModel() {
    const selectedChatModel = customModel.trim() || chatModel;
    if (!selectedChatModel.trim()) return;

    setLoading(true);
    setSaveResult(null);
    try {
      const response = await fetch(`${API}/api/v1/ai/local-models/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_model: selectedChatModel,
          embedding_model: embeddingModel,
          base_url: baseUrl,
        }),
      });
      const data = (await response.json()) as ActionResult;
      setSaveResult(data);
      await load();
      setCustomModel('');
    } catch (error) {
      setSaveResult({ ok: false, error: error instanceof Error ? error.message : 'Unable to save local model' });
    } finally {
      setLoading(false);
    }
  }

  async function toggleExternal() {
    setLoading(true);
    try {
      const response = await fetch(`${API}/api/v1/ai/consent/external-ai`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enable_external: enable, consent_text: consentText }),
      });
      setSaveResult((await response.json()) as ActionResult);
      await load();
    } finally {
      setLoading(false);
    }
  }

  async function test() {
    setLoading(true);
    setTestResult(null);
    try {
      const response = await fetch(`${API}/api/v1/ai/test`, { method: 'POST' });
      setTestResult((await response.json()) as ActionResult);
    } catch (error) {
      setTestResult({ ok: false, error: error instanceof Error ? error.message : 'Connection test failed' });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="AI settings"
        title="Choose local models without weakening privacy"
        description="Ollama remains the default path. External providers require explicit consent, redaction, and audit logging."
        actions={
          <span className="pill border-emerald-900 bg-emerald-950 text-emerald-300">
            <ShieldCheck className="h-3.5 w-3.5" /> Redaction required
          </span>
        }
      />

      <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <MetricCard label="Provider" value={status?.provider || '...'} detail="single AI gateway path" icon={Cpu} tone="text-cyan-300" />
        <MetricCard label="Chat model" value={status?.chat_model || '...'} detail="selected local tag" icon={Bot} />
        <MetricCard label="Installed models" value={modelInfo?.installed_models?.length || 0} detail="reported by Ollama" icon={PlugZap} tone="text-violet-300" />
        <MetricCard
          label="External AI"
          value={status?.external_enabled ? 'Enabled' : 'Disabled'}
          detail="opt-in only"
          icon={ShieldCheck}
          tone={status?.external_enabled ? 'text-amber-300' : 'text-emerald-300'}
        />
      </section>

      <SafetyNotice tone={status?.external_enabled ? 'warning' : 'success'}>
        External AI is {status?.external_enabled ? 'enabled' : 'disabled'}. Local model selection is restricted to localhost-style Ollama endpoints.
      </SafetyNotice>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="card">
          <SectionHeader
            title="Local model"
            description="Select an installed tag, use a suggested tag, or enter a custom pulled Ollama model."
            action={
              <button className="btn btn-secondary px-3 py-1.5" onClick={load} disabled={loading}>
              <RefreshCcw className="h-4 w-4" /> Refresh
              </button>
            }
          />

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="text-sm">
              <span className="mb-2 block text-zinc-400">Chat model</span>
              <select
                className="input"
                value={selectableModels.includes(chatModel) ? chatModel : 'custom'}
                onChange={(event) => {
                  const nextValue = event.target.value;
                  if (nextValue === 'custom') {
                    setCustomModel(chatModel);
                  } else {
                    setChatModel(nextValue);
                    setCustomModel('');
                  }
                }}
              >
                {selectableModels.map((model) => (
                  <option key={model} value={model}>
                    {model === 'custom' ? 'Custom local tag' : model}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm">
              <span className="mb-2 block text-zinc-400">Embedding model</span>
              <input className="input" value={embeddingModel} onChange={(event) => setEmbeddingModel(event.target.value)} />
            </label>
            <label className="text-sm md:col-span-2">
              <span className="mb-2 block text-zinc-400">Custom chat model</span>
              <input
                className="input"
                value={customModel}
                onChange={(event) => setCustomModel(event.target.value)}
                placeholder="gemma3:4b, qwen2.5:7b, mistral:7b, or any pulled Ollama tag"
              />
            </label>
            <label className="text-sm md:col-span-2">
              <span className="mb-2 block text-zinc-400">Ollama base URL</span>
              <input className="input" value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)} />
            </label>
          </div>

          <div className="mt-5 flex flex-wrap gap-2">
            <button className="btn btn-primary" onClick={saveLocalModel} disabled={loading || !(customModel.trim() || chatModel.trim())}>
              <Save className="h-4 w-4" /> Save local model
            </button>
            <button className="btn btn-secondary" onClick={test} disabled={loading}>
              <PlugZap className="h-4 w-4" /> Test provider
            </button>
          </div>

          {saveResult && (
            <div className={`mt-4 rounded-lg border p-3 text-sm ${saveResult.ok ? 'border-emerald-900 bg-emerald-950/30 text-emerald-200' : 'border-red-900 bg-red-950/30 text-red-200'}`}>
              <div className="flex items-start gap-2">
                {saveResult.ok ? <CheckCircle2 className="mt-0.5 h-4 w-4" /> : <TriangleAlert className="mt-0.5 h-4 w-4" />}
                <div>
                  <div>{saveResult.ok ? `${saveResult.chat_model || chatModel} selected` : saveResult.error || 'Unable to update local model'}</div>
                  {saveResult.warning && <div className="mt-1 text-xs opacity-80">{saveResult.warning}</div>}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <section className="card">
            <SectionHeader title="Installed local tags" description="Click a tag to stage it for selection." />
            {modelInfo?.installed_models?.length ? (
              <div className="flex flex-wrap gap-2">
                {modelInfo.installed_models.map((model) => (
                  <button
                    key={model}
                    className={`pill ${model === status?.chat_model ? 'border-emerald-900 bg-emerald-950 text-emerald-300' : 'border-zinc-800 bg-zinc-950 text-zinc-300'}`}
                    onClick={() => {
                      setChatModel(model);
                      setCustomModel('');
                    }}
                  >
                    {model}
                  </button>
                ))}
              </div>
            ) : (
              <EmptyState icon={Bot} title="No local tags reported" description="Start Ollama and pull a model tag, then refresh this page." />
            )}
          </section>

          <section className="card">
            <SectionHeader title="Suggested local tags" description="These are examples only; use any local tag you have pulled." />
            <div className="flex flex-wrap gap-2">
              {(modelInfo?.suggested_models || []).map((model) => (
                <button
                  key={model}
                  className="pill border-zinc-800 bg-zinc-950 text-zinc-300 hover:border-zinc-700"
                  onClick={() => {
                    setChatModel(model);
                    setCustomModel('');
                  }}
                >
                  {model}
                </button>
              ))}
            </div>
          </section>

          <section className="card">
            <SectionHeader title="Connection test" description="Verify the active local provider path before relying on generation." />
            {testResult ? (
              <pre className="overflow-auto rounded-lg bg-black p-3 text-xs text-zinc-300">{JSON.stringify(testResult, null, 2)}</pre>
            ) : (
              <p className="text-sm text-zinc-500">No test run yet.</p>
            )}
          </section>
        </div>
      </section>

      <section className="card">
        <SectionHeader title="External AI consent" description="External AI stays disabled by default. Enabling it requires consent, redaction, and audit logging." />
        <ProgressBar value={enable ? 66 : 33} tone={enable ? 'bg-amber-300' : 'bg-emerald-300'} label="consent gate readiness" />
        <label className="flex items-center gap-2 text-sm mb-3">
          <input type="checkbox" checked={enable} onChange={(event) => setEnable(event.target.checked)} /> Enable external providers after consent
        </label>
        <textarea value={consentText} onChange={(event) => setConsentText(event.target.value)} className="input h-20 text-xs mb-3" />
        <button onClick={toggleExternal} className="btn btn-secondary" disabled={loading}>
          <ShieldCheck className="h-4 w-4" /> Record Consent &amp; Update
        </button>
        <div className="disclaimer">PII redaction runs before any external call. All calls audited. You can revoke anytime.</div>
      </section>
    </div>
  );
}
