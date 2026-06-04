"""
Concrete Ollama local provider.

Implements chat / structured / embed / stream against Ollama HTTP API
with proper timeouts, error mapping, streaming support.

Local-only; never used for external paths.
All calls from gateway (redaction/audit/consent already handled there).
"""

import json
from typing import Any, Dict, List, Optional, AsyncIterator

import httpx


class OllamaProvider:
    """Thin, robust wrapper over Ollama's /api/* endpoints."""

    def __init__(
        self,
        base_url: str,
        chat_model: str,
        embed_model: str,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.chat_model = chat_model
        self.embed_model = embed_model
        # Separate timeouts: connect short, overall longer for generation
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=10.0, read=timeout),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            headers={"Content-Type": "application/json"},
        )

    async def aclose(self) -> None:
        await self.client.aclose()

    async def _request(
        self, method: str, path: str, *, json: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        url = f"{self.base_url}{path}"
        try:
            if method.upper() == "GET":
                resp = await self.client.get(url)
            else:
                resp = await self.client.post(url, json=json or {})
            resp.raise_for_status()
            return resp
        except httpx.HTTPStatusError as exc:
            body = ""
            try:
                body = exc.response.text[:500]
            except Exception:
                pass
            raise RuntimeError(
                f"Ollama HTTP {exc.response.status_code} {path}: {body}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"Ollama timeout on {path} (>{self.client.timeout})"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Ollama connection error {path} (base_url={self.base_url}): {exc}. "
                "Is ollama running? Check docker compose or local ollama serve."
            ) from exc

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Non-stream or buffered stream result."""
        model = model or self.chat_model
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": bool(stream),
            "options": {
                "temperature": float(temperature),
                "num_predict": int(max_tokens),
            },
        }
        resp = await self._request("POST", "/api/chat", json=payload)

        if stream:
            content = ""
            usage = {"prompt_tokens": 0, "completion_tokens": 0}
            async for line in resp.aiter_lines():
                if not line or not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                    msg = chunk.get("message") or {}
                    if "content" in msg:
                        content += msg["content"]
                    if "prompt_eval_count" in chunk:
                        usage["prompt_tokens"] = chunk.get("prompt_eval_count", 0)
                    if "eval_count" in chunk:
                        usage["completion_tokens"] = chunk.get("eval_count", 0)
                except Exception:
                    # tolerate partial ndjson
                    continue
            return {"content": content, "usage": usage, "provider": "ollama"}

        data = resp.json()
        content = (data.get("message") or {}).get("content", "")
        usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
        }
        return {"content": content, "usage": usage, "provider": "ollama"}

    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """True delta streaming (yields content chunks as they arrive)."""
        model = model or self.chat_model
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": float(temperature),
                "num_predict": int(max_tokens),
            },
        }
        url = f"{self.base_url}/api/chat"
        try:
            async with self.client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                        msg = chunk.get("message") or {}
                        delta = msg.get("content", "")
                        if delta:
                            yield delta
                    except Exception:
                        continue
        except httpx.HTTPStatusError as exc:
            body = ""
            try:
                body = (await exc.response.aread()).decode()[:200]
            except Exception:
                pass
            raise RuntimeError(
                f"Ollama stream HTTP {exc.response.status_code}: {body}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise RuntimeError("Ollama stream timeout") from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"Ollama stream connection error: {exc}") from exc

    async def structured(
        self,
        system: str,
        user: str,
        schema: Dict[str, Any],
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Structured via chat + json parse (Ollama has no native json mode in all versions)."""
        model = model or self.chat_model
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": user
                + "\n\nReturn ONLY valid JSON matching the requested structure. No prose.",
            },
        ]
        res = await self.chat(
            messages,
            model=model,
            temperature=0.1,
            max_tokens=2048,
            stream=False,
        )
        raw = res.get("content", "").strip()
        try:
            # Strip possible ```json fences
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1] if "```" in raw else raw
                if raw.lower().startswith("json"):
                    raw = raw[4:].strip()
            parsed = json.loads(raw)
            return parsed
        except Exception:
            return {"_raw": raw, "_parse_error": True}

    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> List[float]:
        model = model or self.embed_model
        resp = await self._request(
            "POST", "/api/embeddings", json={"model": model, "prompt": text}
        )
        data = resp.json()
        emb = data.get("embedding") or data.get("embeddings")
        if isinstance(emb, list) and emb and isinstance(emb[0], list):
            emb = emb[0]  # some versions
        return emb or []

    async def list_models(self) -> List[str]:
        """Return model names from /api/tags. Used for health + conn test."""
        resp = await self._request("GET", "/api/tags")
        data = resp.json()
        models = data.get("models", [])
        names: List[str] = []
        for m in models:
            name = m.get("name") or m.get("model")
            if name:
                names.append(name)
        return names

    async def ping(self) -> Dict[str, Any]:
        """Light health for readiness."""
        try:
            models = await self.list_models()
            return {"ok": True, "models": models}
        except Exception as e:
            return {"ok": False, "error": str(e)}
