from __future__ import annotations

import asyncio
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field

from app.ai.gateway import gateway
from app.core.config import settings


class GatewayChatModel(BaseChatModel):
    """LangChain chat model adapter that delegates to ReboundIQ AIGateway."""

    model_name: str = Field(default_factory=lambda: settings.AI_CHAT_MODEL)
    temperature: float = 0.2
    max_tokens: int = 2048
    user_id: str | None = None
    request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def _llm_type(self) -> str:
        return "reboundiq_gateway"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "provider": settings.AI_PROVIDER,
            "gateway": "AIGateway",
        }

    def bind_request(
        self,
        *,
        user_id: str | None,
        request_id: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> "GatewayChatModel":
        return self.model_copy(
            update={
                "user_id": user_id,
                "request_id": request_id,
                "metadata": {**self.metadata, **(metadata or {})},
            }
        )

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._agenerate(messages, stop=stop, **kwargs))
        raise RuntimeError("GatewayChatModel sync generation cannot run inside an event loop")

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        result = await gateway.chat(
            self._to_gateway_messages(messages),
            model=kwargs.get("model") or self.model_name,
            temperature=float(kwargs.get("temperature", self.temperature)),
            max_tokens=int(kwargs.get("max_tokens", self.max_tokens)),
            user_id=self.user_id,
            request_id=self.request_id,
            metadata={**self.metadata, "langchain_adapter": True, "stop": stop or []},
        )
        msg = AIMessage(
            content=result.get("content", ""),
            response_metadata={
                "provider": result.get("provider"),
                "latency_ms": result.get("latency_ms"),
                "usage": result.get("usage", {}),
            },
        )
        return ChatResult(
            generations=[ChatGeneration(message=msg)],
            llm_output={
                "provider": result.get("provider"),
                "usage": result.get("usage", {}),
            },
        )

    def _to_gateway_messages(self, messages: list[BaseMessage]) -> list[dict[str, str]]:
        converted: list[dict[str, str]] = []
        for msg in messages:
            msg_type = getattr(msg, "type", "human")
            role = {
                "human": "user",
                "ai": "assistant",
                "system": "system",
                "tool": "tool",
            }.get(msg_type, "user")
            converted.append({"role": role, "content": self._content_to_text(msg.content)})
        return converted

    def _content_to_text(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, dict):
                    parts.append(str(block.get("text") or block.get("content") or block))
                else:
                    parts.append(str(block))
            return "\n".join(parts)
        return str(content)

