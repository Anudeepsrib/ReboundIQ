import os

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/testdb")
os.environ.setdefault(
    "JWT_SECRET", "test-jwt-secret-that-is-at-least-32-chars-long-for-tests"
)
os.environ.setdefault("ENCRYPTION_KEY", "test-fernet-key-32-bytes-exactly!!")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


def test_agents_router_imports():
    from app.api.v1.endpoints.agents import router

    paths = [route.path for route in router.routes]
    assert "/campaigns" in paths
    assert "/campaigns/{campaign_id}/run" in paths
    assert "/approvals/{approval_id}/decide" in paths


def test_compliance_guard_blocks_unsafe_language():
    from app.agents.compliance import run_compliance_guard

    report = run_compliance_guard(
        artifact_type="outreach_email",
        content={"draft": "This will guarantee an offer and it is H1B safe."},
        citations=[],
    )
    assert not report.passed
    codes = {finding.code for finding in report.findings}
    assert "forbidden_guarantee" in codes
    assert "immigration_advice" in codes


def test_deep_agent_capabilities_available():
    from app.agents.deep_harness import deep_agent_capabilities

    caps = deep_agent_capabilities()
    assert "resume_deep" in caps["subagents"]
    assert "compliance_guard" in caps["subagents"]


@pytest.mark.asyncio
async def test_gateway_structured_uses_chat_audit_path(monkeypatch):
    from app.ai.gateway import AIGateway

    gw = AIGateway()
    calls = []

    async def fake_chat(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
        return {"content": '{"ok": true}', "provider": "test", "usage": {}}

    monkeypatch.setattr(gw, "chat", fake_chat)
    result = await gw.structured(
        "Return JSON.",
        "ping",
        schema={"type": "object"},
        user_id="user-123",
        request_id="req-test",
    )

    assert result == {"ok": True}
    assert calls
    assert calls[0]["kwargs"]["metadata"]["operation"] == "structured"


@pytest.mark.asyncio
async def test_gateway_chat_model_adapter(monkeypatch):
    from langchain_core.messages import HumanMessage

    from app.agents import local_model
    from app.agents.local_model import GatewayChatModel

    async def fake_chat(messages, **kwargs):
        assert messages == [{"role": "user", "content": "hello"}]
        assert kwargs["user_id"] == "user-123"
        return {
            "content": "hi",
            "provider": "test",
            "latency_ms": 1,
            "usage": {"prompt_tokens": 1},
        }

    monkeypatch.setattr(local_model.gateway, "chat", fake_chat)
    model = GatewayChatModel().bind_request(
        user_id="user-123",
        request_id="req-123",
        metadata={"test": True},
    )
    result = await model._agenerate([HumanMessage(content="hello")])

    assert result.generations[0].message.content == "hi"
    assert result.llm_output["provider"] == "test"

