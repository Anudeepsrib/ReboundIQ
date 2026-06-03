"""
Provider-neutral AI Gateway for ReboundIQ.
ALL AI calls MUST go through here. No direct provider calls in business/services/endpoints.
Full: chat, structured, embed, rerank (stub), stream (buffered).
Enforces: local-first (ollama default), redaction (non-bypassable) before ANY external,
consent gate, request_id/user_id propagation, audit to logger + ai_requests model (PR-4).
"""

import json
import time
import httpx
from typing import Any, Dict, List, Optional, AsyncIterator
from app.core.config import settings
from app.core.logging import logger
from .redaction import redaction_service
# from app.models.ai_request import AIRequestLog  # model added; insert wired in later slice via DB dep


class AIGateway:
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.chat_model = settings.AI_CHAT_MODEL
        self.embed_model = settings.AI_EMBEDDING_MODEL
        self.base_url = settings.AI_BASE_URL.rstrip("/")
        self.enable_external = settings.ENABLE_EXTERNAL_AI
        self.client = httpx.AsyncClient(timeout=120.0)

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

        if self.provider == "ollama":
            payload = {
                "model": model,
                "messages": redacted_messages,
                "stream": stream,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            }
            url = f"{self.base_url}/api/chat"
            resp = await self.client.post(url, json=payload)
            resp.raise_for_status()
            if stream:
                # Buffered support for stream flag (real delta streaming in response layer later).
                # Consume lines; last message has final.
                content = ""
                usage = {"prompt_tokens": 0, "completion_tokens": 0}
                async for line in resp.aiter_lines():
                    if line and line.strip():
                        try:
                            chunk = json.loads(line)
                            if "message" in chunk:
                                content += chunk["message"].get("content", "")
                            if "prompt_eval_count" in chunk:
                                usage["prompt_tokens"] = chunk.get(
                                    "prompt_eval_count", 0
                                )
                            if "eval_count" in chunk:
                                usage["completion_tokens"] = chunk.get("eval_count", 0)
                        except Exception:
                            pass
            else:
                data = resp.json()
                content = data.get("message", {}).get("content", "")
                usage = {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                }
        else:
            # External path (litellm compat or direct). Redaction already applied above.
            url = (
                f"{self.base_url}/v1/chat/completions"
                if "openai" in self.provider
                or "litellm" in self.provider
                or settings.AI_BASE_URL
                else "https://api.openai.com/v1/chat/completions"
            )
            headers: Dict[str, str] = {}
            if settings.OPENAI_API_KEY and "openai" in self.provider:
                headers["Authorization"] = f"Bearer {settings.OPENAI_API_KEY}"
            # In full: litellm.acompletion(...) with fallbacks/retries/circuit
            payload = {
                "model": model,
                "messages": redacted_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream,
            }
            resp = await self.client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

        latency = (time.time() - start) * 1000

        # Always audit every request (local + external). request_id propagated from middleware.
        audit_record = {
            "provider": self.provider,
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
        }
        logger.info("ai.chat", extra=audit_record)
        # TODO (next slice): await insert AIRequestLog(..., full_audit_jsonb=audit_record)

        return {
            "content": content,
            "usage": usage,
            "latency_ms": latency,
            "provider": self.provider,
        }

    async def structured(
        self,
        system: str,
        user: str,
        schema: Dict[str, Any],  # JSON schema
        model: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Structured JSON output (via chat + parse for local compat). Redaction/audit via chat."""
        model = model or self.chat_model
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        # For Ollama + many local: use prompt engineering + json.loads (robust in real with retries)
        # For OpenAI: response_format={"type": "json_object", "schema": schema} or tools
        result = await self.chat(
            messages,
            model=model,
            temperature=0.1,
            user_id=user_id,
            request_id=request_id,
        )
        try:
            parsed = json.loads(result["content"])
            return parsed
        except Exception:
            logger.warning(
                "structured.parse_fail",
                extra={"raw": result["content"][:200], "request_id": request_id},
            )
            # Fallback: return raw for caller to handle or retry
            return {"_raw": result["content"], "_parse_error": True}

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
            red_text, was_red, red_audit = await redaction_service.redact_for_external(
                [], user_text=text
            )
            redaction_info = {
                "redacted": was_red,
                "counts": red_audit.get("redaction_counts", {}),
            }

        if self.provider == "ollama":
            url = f"{self.base_url}/api/embeddings"
            r = await self.client.post(url, json={"model": model, "prompt": red_text})
            r.raise_for_status()
            emb = r.json().get("embedding", [])
        else:
            # External embed path (e.g. openai /embeddings) - redacted already
            url = f"{self.base_url}/v1/embeddings"
            headers = {}
            if settings.OPENAI_API_KEY and "openai" in self.provider:
                headers["Authorization"] = f"Bearer {settings.OPENAI_API_KEY}"
            r = await self.client.post(
                url, json={"model": model, "input": red_text}, headers=headers
            )
            r.raise_for_status()
            emb = r.json()["data"][0]["embedding"]

        latency = (time.time() - start) * 1000
        audit_record = {
            "provider": self.provider,
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
        }
        logger.info("ai.embed", extra=audit_record)

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
            _, _, q_audit = await redaction_service.redact_for_external(
                [], user_text=query
            )
            red_docs = []
            doc_counts: Dict[str, int] = {}
            for d in documents:
                rd, dc = redaction_service.redact_text(d)
                red_docs.append(rd)
                for k, v in dc.items():
                    doc_counts[k] = doc_counts.get(k, 0) + v
            redaction_info = {
                "redacted": bool(q_audit.get("redaction_counts") or doc_counts),
                "counts": {**q_audit.get("redaction_counts", {}), **doc_counts},
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
        """Streaming chat deltas. For skeleton: yields from buffered chat (real impl uses aiter in provider)."""
        # In full: use stream=True + yield chunks from ollama ndjson or litellm.
        # Here delegate + simulate single yield for compat in evals/tests.
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


gateway = AIGateway()
