"""Seed the polished ReboundIQ demo persona.

The source fixture is docs/demo/reboundiq_demo_persona.json. It is synthetic and
safe to reset because the email lives under reboundiq.local.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models import (
    AIRequest,
    ActionAuditLog,
    AgentApprovalRequest,
    AgentCampaign,
    AgentToolCall,
    ApplicationRecord,
    ConsentRecord,
    DocumentChunk,
    InterviewSession,
    ProofAsset,
    Resume,
    ResumeVersion,
    RunwaySnapshot,
    UserProfile,
)
from app.services.ai_preferences import save_ai_preferences
from app.services.auth import create_user_with_profile, get_user_by_email
from app.services.privacy import delete_user_account
from app.services.storage import get_storage


REPO_ROOT = Path(__file__).resolve().parents[3]
DEMO_DATA_PATH = REPO_ROOT / "docs" / "demo" / "reboundiq_demo_persona.json"


def load_demo_data(path: Path = DEMO_DATA_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


async def reset_demo_user(email: str) -> None:
    async with AsyncSessionLocal() as db:
        existing = await get_user_by_email(db, email)
        if existing:
            await delete_user_account(db, existing.id, "seed-demo-reset")


async def seed_demo() -> dict[str, Any]:
    data = load_demo_data()
    persona = data["persona"]
    await reset_demo_user(persona["email"])

    async with AsyncSessionLocal() as db:
        user = await create_user_with_profile(
            db,
            email=persona["email"],
            password=persona["password"],
            full_name=persona["full_name"],
        )

        profile = await db.scalar(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        if profile is None:
            profile = UserProfile(user_id=user.id)
            db.add(profile)
            await db.flush()
        profile.headline = persona["headline"]
        profile.summary = persona["summary"]
        profile.skills_json = persona["skills"]
        profile.preferences_json = persona["preferences"]
        profile.sensitive_json = {
            "demo_note": (
                "No sensitive legal, immigration, tax, financial, or medical facts "
                "are inferred."
            ),
        }
        profile.consent_external_ai = bool(persona["consents"]["external_ai"])
        profile.consent_memory_sensitive = bool(persona["consents"]["memory_sensitive"])
        profile.consent_visa_processing = bool(persona["consents"]["visa_processing"])
        ai_settings = persona["preferences"]["ai_settings"]
        await save_ai_preferences(
            db,
            user.id,
            chat_model=ai_settings["chat_model"],
            embedding_model=ai_settings["embedding_model"],
            base_url=ai_settings["base_url"],
        )
        await db.commit()

        resume_data = data["resume"]
        storage_key = f"users/{user.id}/resumes/{resume_data['original_filename']}"
        await get_storage().save(
            storage_key,
            resume_data["parsed_text"].encode("utf-8"),
            resume_data["mime_type"],
        )
        resume = Resume(
            user_id=user.id,
            original_filename=resume_data["original_filename"],
            storage_key=storage_key,
            mime_type=resume_data["mime_type"],
            parsed_text=resume_data["parsed_text"],
            parsed_json=resume_data["parsed_json"],
        )
        db.add(resume)
        await db.flush()

        for chunk in resume_data["chunks"]:
            db.add(
                DocumentChunk(
                    user_id=user.id,
                    resume_id=resume.id,
                    chunk_index=chunk["chunk_index"],
                    text=chunk["text"],
                    embedding=None,
                    meta=chunk["meta"],
                )
            )

        resume_versions: dict[str, ResumeVersion] = {}
        for version in resume_data["versions"]:
            record = ResumeVersion(
                resume_id=resume.id,
                user_id=user.id,
                version_name=version["version_name"],
                target_role=version["target_role"],
                content_json=version["content_json"],
                ats_score=version["ats_score"],
                source_inputs=version["source_inputs"],
            )
            db.add(record)
            await db.flush()
            resume_versions[version["key"]] = record

        for snapshot in data["runway_snapshots"]:
            db.add(RunwaySnapshot(user_id=user.id, **snapshot))

        applications: dict[str, ApplicationRecord] = {}
        for application in data["applications"]:
            payload = dict(application)
            key = payload.pop("key")
            resume_version_key = payload.pop("resume_version_key", None)
            payload["resume_version_id"] = (
                resume_versions[resume_version_key].id if resume_version_key else None
            )
            payload["next_step_at"] = parse_dt(payload.get("next_step_at"))
            record = ApplicationRecord(user_id=user.id, **payload)
            db.add(record)
            await db.flush()
            applications[key] = record

        for asset in data["proof_assets"]:
            payload = dict(asset)
            linked_key = payload.pop("linked_application_key", None)
            payload["linked_application_id"] = (
                applications[linked_key].id if linked_key else None
            )
            db.add(ProofAsset(user_id=user.id, **payload))

        for interview in data["interviews"]:
            payload = dict(interview)
            linked_key = payload.pop("linked_application_key", None)
            payload["linked_application_id"] = (
                applications[linked_key].id if linked_key else None
            )
            payload["scheduled_at"] = parse_dt(payload.get("scheduled_at"))
            db.add(InterviewSession(user_id=user.id, **payload))

        campaign_data = data["campaign"]
        campaign = AgentCampaign(
            user_id=user.id,
            goal=campaign_data["goal"],
            status=campaign_data["status"],
            metadata_json=campaign_data["metadata_json"],
        )
        db.add(campaign)
        await db.flush()

        for approval in campaign_data["approval_requests"]:
            db.add(
                AgentApprovalRequest(
                    user_id=user.id,
                    campaign_id=campaign.id,
                    artifact_type=approval["artifact_type"],
                    artifact_json=approval["artifact_json"],
                    artifact_ref=approval["artifact_ref"],
                    status=approval["status"],
                    notes=approval["notes"],
                )
            )

        for tool_call in campaign_data["tool_calls"]:
            db.add(
                AgentToolCall(
                    user_id=user.id,
                    campaign_id=campaign.id,
                    **tool_call,
                )
            )

        now = datetime.now(timezone.utc)
        for consent in data["consent_records"]:
            db.add(
                ConsentRecord(
                    user_id=user.id,
                    consent_type=consent["consent_type"],
                    granted=consent["granted"],
                    consent_text=consent["consent_text"],
                    revoked_at=parse_dt(consent["revoked_at"]),
                )
            )

        for audit in data["ai_audit_samples"]:
            db.add(AIRequest(user_id=user.id, **audit))

        db.add(
            ActionAuditLog(
                user_id=user.id,
                action="seed_demo",
                resource_type="demo_persona",
                resource_id=user.id,
                request_id="seed-demo",
                metadata_json={
                    "schema_version": data["schema_version"],
                    "seeded_at": now.isoformat(),
                    "screenshot_count": len(data["screenshots"]),
                },
            )
        )
        await db.commit()

        return {
            "email": persona["email"],
            "password": persona["password"],
            "user_id": user.id,
            "applications": len(applications),
            "screenshots": len(data["screenshots"]),
        }


async def main() -> None:
    result = await seed_demo()
    print("Seeded ReboundIQ local-first demo persona.")
    print(f"Email: {result['email']}")
    print(f"Password: {result['password']}")
    print(f"Applications: {result['applications']}")
    print(f"Screenshots documented: {result['screenshots']}")
    print("Open http://localhost:3000/dashboard after login.")


if __name__ == "__main__":
    asyncio.run(main())
