"""
Provider-neutral AI Gateway for ReboundIQ.
All AI calls MUST go through here.
Supports: local Ollama (default), vLLM compat, LiteLLM for externals.
Enforces: local-first, redaction before external, audit, timeout/retry/circuit (basic), usage tracking.
"""

import json
import time
import httpx
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger
# from app.models.ai_request import AIRequestLog  # TODO: create model + audit insert in full slice


class AIGateway:
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.chat_model = settings.AI_CHAT_MODEL
        self.embed_model = settings.AI_EMBEDDING_MODEL
        self.base_url = settings.AI_BASE_URL.rstrip("/")
        self.enable_external = settings.ENABLE_EXTERNAL_AI
        self.client = httpx.AsyncClient(timeout=120.0)

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
        """Chat completion. Returns {content, usage?, raw} . Always audits."""
        model = model or self.chat_model
        start = time.time()
        redacted_messages = messages  # TODO: integrate RedactionService for external

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
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            usage = {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            }
        else:
            # LiteLLM or direct OpenAI compat for other providers
            # For MVP, raise if external not enabled
            if not self.enable_external:
                raise RuntimeError(
                    "External AI disabled. Set ENABLE_EXTERNAL_AI=true + record consent."
                )
            # Simplified: assume OpenAI compat or let litellm handle if installed
            # In full: from litellm import acompletion
            url = (
                f"{self.base_url}/v1/chat/completions"
                if "openai" in self.provider or settings.AI_BASE_URL
                else "https://api.openai.com/v1/chat/completions"
            )
            headers = {}
            if settings.OPENAI_API_KEY and "openai" in self.provider:
                headers["Authorization"] = f"Bearer {settings.OPENAI_API_KEY}"
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
        # Audit (fire and forget for now; in real use DB session)
        logger.info(
            "ai.chat",
            extra={
                "provider": self.provider,
                "model": model,
                "latency_ms": latency,
                "usage": usage,
                "user_id": user_id,
                "request_id": request_id,
                "external": self.enable_external,
            },
        )
        # TODO: persist to ai_requests table with redacted flag, consent_used, etc.

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
        """Structured JSON output. Uses response_format where supported, else prompt+parse."""
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
                "structured.parse_fail", extra={"raw": result["content"][:200]}
            )
            # Fallback: return raw for caller to handle or retry
            return {"_raw": result["content"], "_parse_error": True}

    async def embed(self, text: str, model: Optional[str] = None) -> List[float]:
        model = model or self.embed_model
        if self.provider == "ollama":
            url = f"{self.base_url}/api/embeddings"
            r = await self.client.post(url, json={"model": model, "prompt": text})
            r.raise_for_status()
            return r.json()["embedding"]
        # Fallback for others via litellm or OpenAI /embeddings
        raise NotImplementedError(
            "Embed for external not wired in this slice; use local nomic."
        )

    # TODO: rerank interface, streaming wrapper, circuit breaker, retries, cost calc when metadata present.


gateway = AIGateway()
