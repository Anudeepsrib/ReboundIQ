import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/testdb")
os.environ.setdefault(
    "JWT_SECRET", "test-jwt-secret-that-is-at-least-32-chars-long-for-tests"
)
os.environ.setdefault("ENCRYPTION_KEY", "test-fernet-key-32-bytes-exactly!!")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


REPO_ROOT = Path(__file__).resolve().parents[3]
DEMO_DATA_PATH = REPO_ROOT / "docs" / "demo" / "reboundiq_demo_persona.json"
RELEASE_CHECKLIST_PATH = REPO_ROOT / "docs" / "DEMO_RELEASE_CHECKLIST.md"


def load_demo_data():
    return json.loads(DEMO_DATA_PATH.read_text(encoding="utf-8"))


def test_demo_persona_covers_layoff_to_offer_workflows():
    from app.schemas.workflows import (
        ApplicationCreate,
        InterviewSessionCreate,
        ProofAssetCreate,
        RunwaySnapshotCreate,
    )

    data = load_demo_data()
    routes = {step["route"] for step in data["journey"]}

    assert data["persona"]["email"].endswith("@reboundiq.local")
    assert data["persona"]["consents"] == {
        "external_ai": False,
        "memory_sensitive": False,
        "visa_processing": False,
    }
    assert {
        "/onboarding",
        "/runway",
        "/resume",
        "/jobs",
        "/applications",
        "/proof",
        "/interview",
        "/campaigns",
        "/settings/ai-providers",
        "/dashboard",
    }.issubset(routes)

    for snapshot in data["runway_snapshots"]:
        RunwaySnapshotCreate(**snapshot)
        assert snapshot["disclaimer_acknowledged"] is True

    version_keys = {version["key"] for version in data["resume"]["versions"]}
    application_keys = {application["key"] for application in data["applications"]}

    for application in data["applications"]:
        payload = dict(application)
        payload.pop("key")
        resume_version_key = payload.pop("resume_version_key")
        assert resume_version_key in version_keys
        ApplicationCreate(**payload)

    for asset in data["proof_assets"]:
        payload = dict(asset)
        linked_key = payload.pop("linked_application_key")
        assert linked_key in application_keys
        ProofAssetCreate(**payload)

    for interview in data["interviews"]:
        payload = dict(interview)
        linked_key = payload.pop("linked_application_key")
        assert linked_key in application_keys
        InterviewSessionCreate(**payload)


def test_demo_screenshots_and_kpis_are_documented():
    data = load_demo_data()
    screenshot_paths = [REPO_ROOT / item["path"] for item in data["screenshots"]]
    workflow_names = {item["workflow"] for item in data["screenshots"]}
    kpi_names = {item["name"] for item in data["outcome_kpis"]}

    assert len(screenshot_paths) >= 9
    assert all(path.exists() for path in screenshot_paths)
    assert {
        "Dashboard command center",
        "AI provider settings",
        "Privacy export and delete",
    }.issubset(workflow_names)
    assert {
        "Human control",
        "Privacy posture",
        "Pipeline health",
    }.issubset(kpi_names)


def test_legal_disclaimers_cover_required_decision_areas():
    disclaimer = load_demo_data()["legal_disclaimer"].lower()
    for term in ("employment", "immigration", "tax", "financial"):
        assert term in disclaimer
    assert "planning guidance" in disclaimer
    assert "qualified professionals" in disclaimer


def test_ai_provider_switching_keeps_local_boundary():
    from app.ai.gateway import AIGateway

    gateway = AIGateway()
    accepted = gateway.validate_local_model_config(
        chat_model="gemma3:4b",
        embedding_model="nomic-embed-text",
        base_url="http://localhost:11434",
    )
    assert accepted["provider"] == "ollama"
    assert accepted["chat_model"] == "gemma3:4b"

    with pytest.raises(ValueError, match="external provider consent flow"):
        gateway.validate_local_model_config(
            chat_model="gemma3:4b",
            embedding_model="nomic-embed-text",
            base_url="https://models.example.com",
        )


def test_export_delete_flows_cover_demo_tables():
    from app.services.privacy import DELETE_MODELS, EXPORT_MODELS

    export_tables = {model.__tablename__ for model in EXPORT_MODELS}
    delete_tables = {model.__tablename__ for model in DELETE_MODELS}
    required_tables = {
        "user_profiles",
        "resumes",
        "resume_versions",
        "document_chunks",
        "agent_campaigns",
        "agent_tool_calls",
        "agent_approval_requests",
        "ai_requests",
        "consent_records",
        "runway_snapshots",
        "application_records",
        "proof_assets",
        "interview_sessions",
        "action_audit_logs",
    }

    assert required_tables.issubset(export_tables)
    assert required_tables.issubset(delete_tables)


def test_release_checklist_keeps_enterprise_demo_gates():
    checklist = RELEASE_CHECKLIST_PATH.read_text(encoding="utf-8")
    for phrase in (
        "make seed",
        "python -m pytest tests -q",
        "npm run build",
        "make eval",
        "remote base URL is rejected",
        "External AI remains disabled",
        "Legal disclaimers",
        "employment, immigration, tax, and financial",
    ):
        assert phrase in checklist
