import os
import subprocess

import pytest
from pydantic import ValidationError

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/testdb")
os.environ.setdefault(
    "JWT_SECRET", "test-jwt-secret-that-is-at-least-32-chars-long-for-tests"
)
os.environ.setdefault("ENCRYPTION_KEY", "test-fernet-key-32-bytes-exactly!!")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


def test_workflow_router_registers_product_paths():
    from app.api.v1.endpoints.workflows import router

    paths = {route.path for route in router.routes}
    assert "/runway/snapshots" in paths
    assert "/applications" in paths
    assert "/proof/assets" in paths
    assert "/interviews/sessions" in paths


def test_workflow_schemas_validate_product_bounds():
    from app.schemas.workflows import (
        ApplicationCreate,
        InterviewSessionCreate,
        ProofAssetCreate,
        RunwaySnapshotCreate,
    )

    app = ApplicationCreate(company="OpenAI", role="Backend Engineer")
    assert app.status == "saved"

    proof = ProofAssetCreate(title="RAG platform story", asset_type="case_study")
    assert proof.status == "draft"

    interview = InterviewSessionCreate(target_role="Staff AI Engineer", score=82)
    assert interview.interview_type == "mixed"

    with pytest.raises(ValidationError):
        RunwaySnapshotCreate(monthly_expenses=-1)
    with pytest.raises(ValidationError):
        InterviewSessionCreate(target_role="Staff AI Engineer", score=120)


def test_owned_active_statement_filters_by_user_and_soft_delete():
    from app.models.workflows import ApplicationRecord
    from app.services.workflows import owned_active_stmt

    stmt = owned_active_stmt(ApplicationRecord, "user-123", "app-123")
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))

    assert "application_records.user_id = 'user-123'" in compiled
    assert "application_records.id = 'app-123'" in compiled
    assert "application_records.deleted_at IS NULL" in compiled


def test_alembic_revision_graph_has_single_head():
    result = subprocess.run(
        ["alembic", "heads"],
        capture_output=True,
        check=True,
        text=True,
    )

    assert result.stdout.strip() == "0006 (head)"
    assert "present more than once" not in result.stderr
