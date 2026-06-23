"""
Provider-neutral AI Gateway for ReboundIQ.
ALL AI calls MUST go through here. No direct provider calls in business/services/endpoints.
Delegates concrete impl (chat/structured/embed/stream) to providers/ (ollama primary for local).
Full: chat, structured, embed, rerank (stub), stream.
Enforces: local-first (ollama default), redaction (non-bypassable) before ANY external,
consent gate, request_id/user_id propagation, audit to logger + ai_requests model (PR-4).
"""

import json
import time
import httpx
from typing import Any, Dict, List, Optional, AsyncIterator
from urllib.parse import urlparse
from app.core.config import settings
from app.core.logging import logger
from .redaction import redaction_service
from .providers.ollama import OllamaProvider
# from app.models.ai_request import AIRequestLog  # model added; insert wired in later slice via DB dep

# LiteLLM for unified external providers (openai, anthropic, groq, gemini, azure, bedrock, custom via litellm proxy etc).
# Only imported/used on external paths (after consent + redaction gate). Local ollama stays direct.
try:
    import litellm  # type: ignore

    # Keep quiet in normal ops; can be overridden via env if needed for debugging specific providers.
    litellm.set_verbose = False
except Exception:  # ImportError or runtime issues in some envs
    litellm = None  # type: ignore


class AIGateway:
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.chat_model = settings.AI_CHAT_MODEL
        self.embed_model = settings.AI_EMBEDDING_MODEL
        self.base_url = settings.AI_BASE_URL.rstrip("/")
        self.enable_external = settings.ENABLE_EXTERNAL_AI
        self.client = httpx.AsyncClient(timeout=120.0)
        self._ollama: Optional["OllamaProvider"] = None
        if self.provider == "ollama":
            self._ollama = OllamaProvider(
                self.base_url, self.chat_model, self.embed_model
            )

    def _is_local_base_url(self, base_url: str) -> bool:
        parsed = urlparse(base_url)
        host = (parsed.hostname or "").lower()
        return host in {
            "localhost",
            "127.0.0.1",
            "::1",
            "ollama",
            "host.docker.internal",
        }

    def configure_local_models(
        self,
        *,
        chat_model: str,
        embedding_model: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runtime demo settings for local Ollama models.

        Persistence belongs in a user settings table in the production slice. This method
        intentionally refuses non-local base URLs to avoid turning local settings into an
        external-provider bypass.
        """
        chat_model = chat_model.strip()
        embedding_model = (embedding_model or self.embed_model).strip()
        next_base_url = (base_url or self.base_url).strip().rstrip("/")

        if not chat_model:
            raise ValueError("chat_model is required")
        if not embedding_model:
            raise ValueError("embedding_model is required")
        if not next_base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        if not self._is_local_base_url(next_base_url):
            raise ValueError(
                "Local model base_url must point to localhost, ollama, or host.docker.internal. "
                "Use the external provider consent flow for remote services."
            )

        self.provider = "ollama"
        self.chat_model = chat_model
        self.embed_model = embedding_model
        self.base_url = next_base_url
        self.enable_external = settings.ENABLE_EXTERNAL_AI
        self._ollama = OllamaProvider(self.base_url, self.chat_model, self.embed_model)

        settings.AI_PROVIDER = "ollama"
        settings.AI_CHAT_MODEL = self.chat_model
        settings.AI_EMBEDDING_MODEL = self.embed_model
        settings.AI_BASE_URL = self.base_url

        return {
            "provider": self.provider,
            "chat_model": self.chat_model,
            "embedding_model": self.embed_model,
            "base_url": self.base_url,
        }

    def validate_local_model_config(
        self,
        *,
        chat_model: str,
        embedding_model: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> Dict[str, str]:
        chat_model = chat_model.strip()
        embedding_model = (embedding_model or settings.AI_EMBEDDING_MODEL).strip()
        next_base_url = (base_url or settings.AI_BASE_URL).strip().rstrip("/")
        if not chat_model:
            raise ValueError("chat_model is required")
        if not embedding_model:
            raise ValueError("embedding_model is required")
        if not next_base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        if not self._is_local_base_url(next_base_url):
            raise ValueError(
                "Local model base_url must point to localhost, ollama, or host.docker.internal. "
                "Use the external provider consent flow for remote services."
            )
        return {
            "provider": "ollama",
            "chat_model": chat_model,
            "embedding_model": embedding_model,
            "base_url": next_base_url,
        }

    def _is_external(self) -> bool:
        """Local (ollama/vllm on localhost) default; anything else or flag = external."""
        return self.provider not in ("ollama", "vllm")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        stream: bool = False,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Chat completion. Returns {content, usage?, latency_ms, provider}. Always redacts + audits."""
        model = model or self.chat_model
        start = time.time()
        is_external = self._is_external()

        if is_external and not self.enable_external:
            raise RuntimeError(
                "External AI disabled. Set ENABLE_EXTERNAL_AI=true + record explicit consent via /ai/consent."
            )

        redacted_messages = messages
        redaction_info: Dict[str, Any] = {
            "redacted": False,
            "counts": {},
            "used_llm_fallback": False,
        }
        if is_external:
            # NON-BYPASSABLE: redaction before any external, even if consent_used.
            (
                redacted_messages,
                was_red,
                red_audit,
            ) = await redaction_service.redact_for_external(messages)
            redaction_info = {
                "redacted": was_red,
                "counts": red_audit.get("redaction_counts", {}),
                "used_llm_fallback": red_audit.get("used_llm_fallback", False),
            }

        content = ""
        usage: Dict[str, Any] = {}
        effective_provider = self.provider
        used_fallback = False

        if self.provider == "ollama":
            if self._ollama is None:
                raise RuntimeError("Ollama provider not initialized")
            prov_res = await self._ollama.chat(
                redacted_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
            )
            content = prov_res["content"]
            usage = prov_res.get("usage", {})
        else:
            # External path: LiteLLM (unified multi-provider) preferred when available.
            # Redaction + consent gate already enforced above (NON-BYPASSABLE).
            # Supports: openai, anthropic, groq, gemini, azure, bedrock, litellm proxy, + custom via env.
            # Fallback: if primary external fails (no key, rate, outage), try AI_FALLBACK_* (local or other).
            call_succeeded = False
            attempts = [
                (self.provider, model, True),
            ]
            fb_prov = settings.AI_FALLBACK_PROVIDER
            if fb_prov:
                fb_model = settings.AI_FALLBACK_MODEL or model
                fb_is_ext = fb_prov not in ("ollama", "vllm")
                attempts.append((fb_prov, fb_model, fb_is_ext))

            for attempt_idx, (att_provider, att_model, att_is_ext) in enumerate(
                attempts
            ):
                if call_succeeded:
                    break
                if attempt_idx > 0:
                    used_fallback = True
                    effective_provider = att_provider
                try:
                    if litellm is not None and att_provider not in ("ollama", "vllm"):
                        # Preferred unified path for external providers (litellm handles multi + keys from env).
                        lparams: Dict[str, Any] = {
                            "model": att_model,
                            "messages": redacted_messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            # stream handled below in full impl; here we use non-stream + buffer for compat
                        }
                        if self.base_url and "api.openai.com" not in self.base_url:
                            lparams["api_base"] = self.base_url
                        if stream:
                            lparams["stream"] = False
                        resp = await litellm.acompletion(**lparams)
                        msg = (
                            resp.choices[0].message
                            if hasattr(resp, "choices")
                            else resp["choices"][0]["message"]
                        )
                        content = getattr(msg, "content", None) or (
                            msg.get("content") if isinstance(msg, dict) else ""
                        )
                        u = getattr(resp, "usage", None) or (
                            resp.get("usage") if isinstance(resp, dict) else {}
                        )
                        if hasattr(u, "model_dump"):
                            usage = u.model_dump()
                        elif isinstance(u, dict):
                            usage = u
                        else:
                            usage = {
                                "prompt_tokens": getattr(u, "prompt_tokens", 0),
                                "completion_tokens": getattr(u, "completion_tokens", 0),
                            }
                        call_succeeded = True
                        break
                    elif att_provider in ("ollama", "vllm"):
                        # Direct ollama/vllm (even on fallback from external). Reuse original payload logic.
                        payload = {
                            "model": att_model,
                            "messages": redacted_messages,
                            "stream": False,
                            "options": {
                                "temperature": temperature,
                                "num_predict": max_tokens,
                            },
                        }
                        url = f"{self.base_url}/api/chat"
                        r = await self.client.post(url, json=payload)
                        r.raise_for_status()
                        data = r.json()
                        content = data.get("message", {}).get("content", "")
                        usage = {
                            "prompt_tokens": data.get("prompt_eval_count", 0),
                            "completion_tokens": data.get("eval_count", 0),
                        }
                        call_succeeded = True
                        break
                    else:
                        # Raw compat HTTP for external when no litellm (or as last resort)
                        url = (
                            f"{self.base_url}/v1/chat/completions"
                            if self.base_url
                            else "https://api.openai.com/v1/chat/completions"
                        )
                        headers: Dict[str, str] = {}
                        if settings.OPENAI_API_KEY and (
                            "openai" in att_provider or "litellm" in att_provider
                        ):
                            headers["Authorization"] = (
                                f"Bearer {settings.OPENAI_API_KEY}"
                            )
                        payload = {
                            "model": att_model,
                            "messages": redacted_messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            "stream": False,
                        }
                        r = await self.client.post(url, json=payload, headers=headers)
                        r.raise_for_status()
                        data = r.json()
                        content = data["choices"][0]["message"]["content"]
                        usage = data.get("usage", {})
                        call_succeeded = True
                        break
                except Exception as ex:
                    logger.warning(
                        "ai.external.attempt_failed",
                        extra={
                            "provider": att_provider,
                            "model": att_model,
                            "fallback": attempt_idx > 0,
                            "error_type": type(ex).__name__,
                            "error": str(ex)[:180],
                            "request_id": request_id,
                        },
                    )
                    continue

            if not call_succeeded:
                raise RuntimeError(
                    f"All AI providers failed (primary={self.provider}, fallback={settings.AI_FALLBACK_PROVIDER}). "
                    "Check ENABLE_EXTERNAL_AI, keys in env (never committed), or ollama health."
                )

        latency = (time.time() - start) * 1000

        # Always audit every request (local + external). request_id propagated from middleware.
        prompt_preview = self._prompt_preview(redacted_messages)
        response_preview = self._redacted_preview(content)
        audit_record = {
            "provider": effective_provider,
            "model": model,
            "endpoint": "chat",
            "user_id": user_id,
            "request_id": request_id,
            "latency_ms": latency,
            "usage": usage,
            "redacted": redaction_info["redacted"],
            "consent_used": bool(self.enable_external and is_external),
            "redaction_counts": redaction_info.get("counts", {}),
            "metadata": metadata or {},
            "external": is_external,
            "used_fallback": used_fallback,
            "primary_provider": self.provider,
        }
        logger.info("ai.chat", extra=audit_record)
        await self._persist_ai_request(
            audit_record,
            prompt_preview=prompt_preview,
            response_preview=response_preview,
        )

        return {
            "content": content,
            "usage": usage,
            "latency_ms": latency,
            "provider": effective_provider,
        }

    async def structured(
        self,
        system: str,
        user: str,
        schema: Dict[str, Any],  # JSON schema
        model: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Structured JSON output (via chat + parse for local compat). Redaction/audit via chat."""
        model = model or self.chat_model
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": user
                + "\n\nReturn ONLY valid JSON matching the requested structure. No prose.",
            },
        ]
        result = await self.chat(
            messages,
            model=model,
            temperature=0.1,
            user_id=user_id,
            request_id=request_id,
            metadata={
                "operation": "structured",
                "schema": schema,
                **(metadata or {}),
            },
        )
        raw = (result.get("content") or "").strip()
        try:
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1] if "```" in raw else raw
                if raw.lower().startswith("json"):
                    raw = raw[4:].strip()
            parsed = json.loads(raw)
            return parsed
        except Exception:
            logger.warning(
                "structured.parse_fail",
                extra={"raw": raw[:200], "request_id": request_id},
            )
            # Fallback: return raw for caller to handle or retry
            return {"_raw": raw, "_parse_error": True}

    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> List[float]:
        """Embeddings. Redacts text if external path (PII can be in docs for RAG). Audits."""
        model = model or self.embed_model
        start = time.time()
        is_external = self._is_external()
        if is_external and not self.enable_external:
            raise RuntimeError("External AI disabled for embeddings.")

        red_text = text
        redaction_info = {"redacted": False, "counts": {}}
        if is_external:
            red_text, counts = redaction_service.redact_text(text)
            redaction_info = {
                "redacted": bool(counts),
                "counts": counts,
            }

        emb: List[float] = []
        effective_provider = self.provider
        used_fallback = False

        if self.provider == "ollama":
            if self._ollama is None:
                raise RuntimeError("Ollama provider not initialized")
            emb = await self._ollama.embed(red_text, model=model)
        else:
            # External embed via LiteLLM (aembedding) + fallback support. Redaction already done.
            call_succeeded = False
            attempts = [(self.provider, model)]
            fb_prov = settings.AI_FALLBACK_PROVIDER
            if fb_prov:
                attempts.append((fb_prov, settings.AI_FALLBACK_MODEL or model))
            for attempt_idx, (att_provider, att_model) in enumerate(attempts):
                if call_succeeded:
                    break
                if attempt_idx > 0:
                    used_fallback = True
                    effective_provider = att_provider
                try:
                    if litellm is not None and att_provider not in ("ollama", "vllm"):
                        eresp = await litellm.aembedding(
                            model=att_model, input=red_text
                        )
                        if hasattr(eresp, "data"):
                            emb = eresp.data[0].embedding
                        else:
                            emb = eresp["data"][0]["embedding"]
                        call_succeeded = True
                        break
                    elif att_provider in ("ollama", "vllm"):
                        # direct for local fallback
                        url = f"{self.base_url}/api/embeddings"
                        r = await self.client.post(
                            url, json={"model": att_model, "prompt": red_text}
                        )
                        r.raise_for_status()
                        emb = r.json().get("embedding", [])
                        call_succeeded = True
                        break
                    else:
                        url = f"{self.base_url}/v1/embeddings"
                        headers = {}
                        if settings.OPENAI_API_KEY and (
                            "openai" in att_provider or "litellm" in att_provider
                        ):
                            headers["Authorization"] = (
                                f"Bearer {settings.OPENAI_API_KEY}"
                            )
                        r = await self.client.post(
                            url,
                            json={"model": att_model, "input": red_text},
                            headers=headers,
                        )
                        r.raise_for_status()
                        emb = r.json()["data"][0]["embedding"]
                        call_succeeded = True
                        break
                except Exception as ex:
                    logger.warning(
                        "ai.embed.attempt_failed",
                        extra={
                            "provider": att_provider,
                            "error_type": type(ex).__name__,
                            "error": str(ex)[:160],
                        },
                    )
                    continue
            if not call_succeeded:
                raise RuntimeError(
                    f"Embed providers failed (primary={self.provider}, fb={settings.AI_FALLBACK_PROVIDER})"
                )

        latency = (time.time() - start) * 1000
        audit_record = {
            "provider": effective_provider,
            "model": model,
            "endpoint": "embed",
            "user_id": user_id,
            "request_id": request_id,
            "latency_ms": latency,
            "usage": {"prompt_tokens": 0},  # embed usage often separate
            "redacted": redaction_info["redacted"],
            "consent_used": bool(self.enable_external and is_external),
            "redaction_counts": redaction_info.get("counts", {}),
            "external": is_external,
            "used_fallback": used_fallback,
            "primary_provider": self.provider,
        }
        logger.info("ai.embed", extra=audit_record)
        await self._persist_ai_request(
            audit_record,
            prompt_preview=self._redacted_preview(red_text),
            response_preview=f"embedding_dim={len(emb)}",
        )

        return emb

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5,
        model: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Rerank stub (local-first; no external reranker yet). Redact query/docs if external."""
        start = time.time()
        is_external = self._is_external()
        if is_external and not self.enable_external:
            raise RuntimeError("External rerank disabled.")

        red_docs = documents
        redaction_info = {"redacted": False, "counts": {}}
        if is_external:
            # redact query + all docs
            _, q_counts = redaction_service.redact_text(query)
            red_docs = []
            doc_counts: Dict[str, int] = {}
            for d in documents:
                rd, dc = redaction_service.redact_text(d)
                red_docs.append(rd)
                for k, v in dc.items():
                    doc_counts[k] = doc_counts.get(k, 0) + v
            redaction_info = {
                "redacted": bool(q_counts or doc_counts),
                "counts": {**q_counts, **doc_counts},
            }

        # Concrete stub: identity order + dummy scores. Real: cross-encoder or cohere/litellm rerank.
        ranked = [
            {"index": i, "doc": d[:200], "score": round(0.95 - (i * 0.05), 4)}
            for i, d in enumerate(red_docs[:top_k])
        ]

        latency = (time.time() - start) * 1000
        audit_record = {
            "provider": self.provider,
            "model": model or "stub-rerank",
            "endpoint": "rerank",
            "user_id": user_id,
            "request_id": request_id,
            "latency_ms": latency,
            "usage": {"documents": len(documents)},
            "redacted": redaction_info["redacted"],
            "consent_used": bool(self.enable_external and is_external),
            "redaction_counts": redaction_info.get("counts", {}),
            "external": is_external,
        }
        logger.info("ai.rerank", extra=audit_record)
        await self._persist_ai_request(
            audit_record,
            prompt_preview=self._redacted_preview(query),
            response_preview=f"ranked={len(ranked)}",
        )
        return ranked

    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Streaming chat deltas. Real deltas for ollama via provider; buffered for others."""
        if self.provider == "ollama":
            if self._ollama is None:
                raise RuntimeError("Ollama provider not initialized")
            async for delta in self._ollama.stream(
                messages,
                model=model or self.chat_model,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                yield delta
            return
        # Fallback for non-ollama (buffered)
        res = await self.chat(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            user_id=user_id,
            request_id=request_id,
        )
        yield res.get("content", "")

    async def local_health(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Connection / readiness for local providers (used by /ready, /ai/status, /ai/test-conn).
        Returns model list etc. Only for ollama path (local mode).
        """
        if self.provider != "ollama" or self._ollama is None:
            return {
                "provider": self.provider,
                "local": False,
                "message": "not local ollama (or not initialized)",
            }
        try:
            models = await self._ollama.list_models()
            chat_model = self.chat_model
            embed_model = self.embed_model
            model_present = any(
                chat_model in m or m.startswith(chat_model.split(":")[0])
                for m in models
            ) or any(
                embed_model in m or m.startswith(embed_model.split(":")[0])
                for m in models
            )
            return {
                "provider": self.provider,
                "local": True,
                "base_url": self.base_url,
                "chat_model": chat_model,
                "embed_model": embed_model,
                "models": models,
                "model_present": model_present,
            }
        except Exception as e:
            return {
                "provider": self.provider,
                "local": True,
                "error": str(e)[:300],
                "base_url": self.base_url,
            }

    def _redacted_preview(self, text: str, *, limit: int = 1200) -> str:
        redacted, _ = redaction_service.redact_text(text or "")
        return redacted[:limit]

    def _prompt_preview(self, messages: List[Dict[str, str]], *, limit: int = 1200) -> str:
        parts: list[str] = []
        for msg in messages or []:
            role = msg.get("role", "unknown") if isinstance(msg, dict) else "unknown"
            content = msg.get("content", "") if isinstance(msg, dict) else ""
            parts.append(f"{role}: {content}")
        return self._redacted_preview("\n".join(parts), limit=limit)

    async def _persist_ai_request(
        self,
        audit_record: Dict[str, Any],
        *,
        prompt_preview: Optional[str],
        response_preview: Optional[str],
    ) -> None:
        """Best-effort DB audit for AI calls with a user_id.

        The structured log above is always emitted. DB persistence is skipped when
        there is no authenticated user or the database is unavailable during smoke
        tests, but failures are logged with request_id for follow-up.
        """
        user_id = audit_record.get("user_id")
        if not user_id:
            return
        try:
            from app.db.session import get_db_context
            from app.models.ai_requests import AIRequest

            async with get_db_context() as db:
                db.add(
                    AIRequest(
                        user_id=str(user_id),
                        request_id=audit_record.get("request_id"),
                        provider=audit_record.get("provider") or self.provider,
                        model=audit_record.get("model") or self.chat_model,
                        prompt_preview=prompt_preview,
                        response_preview=response_preview,
                        usage_json={
                            "usage": audit_record.get("usage", {}),
                            "endpoint": audit_record.get("endpoint"),
                            "latency_ms": audit_record.get("latency_ms"),
                            "redaction_counts": audit_record.get(
                                "redaction_counts", {}
                            ),
                            "used_fallback": audit_record.get("used_fallback", False),
                            "metadata": audit_record.get("metadata", {}),
                        },
                        external=bool(audit_record.get("external", False)),
                        redacted=bool(audit_record.get("redacted", False)),
                        consent_id=None,
                    )
                )
        except Exception as ex:
            logger.warning(
                "ai.audit.persist_failed",
                extra={
                    "request_id": audit_record.get("request_id"),
                    "user_id": user_id,
                    "error_type": type(ex).__name__,
                    "error": str(ex)[:180],
                },
            )


gateway = AIGateway()
