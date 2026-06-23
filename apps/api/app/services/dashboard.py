from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume, ResumeVersion
from app.models.workflows import (
    ApplicationRecord,
    InterviewSession,
    ProofAsset,
    RunwaySnapshot,
)

ACTIVE_APPLICATION_STATUSES = {
    "saved",
    "applied",
    "recruiter",
    "tech",
    "system_design",
    "manager",
    "final",
}
INTERVIEW_APPLICATION_STATUSES = {"tech", "system_design", "manager", "final"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _latest(items: list[Any]) -> Any | None:
    return items[0] if items else None


def _runway_months(snapshot: RunwaySnapshot | None) -> float | None:
    if not snapshot or not snapshot.monthly_expenses:
        return None
    available = (
        float(snapshot.savings_balance or 0)
        + float(snapshot.severance_amount or 0)
        + float(snapshot.unemployment_amount or 0)
    )
    return round(available / max(float(snapshot.monthly_expenses), 1), 1)


def _runway_risk(months: float | None) -> str:
    if months is None:
        return "unknown"
    if months < 2:
        return "critical"
    if months < 4:
        return "high"
    if months < 6:
        return "moderate"
    return "stable"


def _readiness(
    *,
    resumes: list[Resume],
    versions: list[ResumeVersion],
    applications: list[ApplicationRecord],
    proof_assets: list[ProofAsset],
    interviews: list[InterviewSession],
    runway_months: float | None,
) -> int:
    score = 0
    if resumes:
        score += 15
    if versions:
        score += 15
    active_apps = [a for a in applications if a.status in ACTIVE_APPLICATION_STATUSES]
    score += min(20, len(active_apps) * 4)
    ready_proof = [p for p in proof_assets if p.status in {"ready", "approved"}]
    score += min(20, len(ready_proof) * 7)
    completed_interviews = [i for i in interviews if i.status == "completed"]
    score += min(15, len(completed_interviews) * 5)
    if runway_months is not None:
        score += 15 if runway_months >= 4 else 8
    return min(100, score)


def _due_applications(applications: list[ApplicationRecord]) -> list[ApplicationRecord]:
    now = _now()
    return [
        app
        for app in applications
        if app.status in ACTIVE_APPLICATION_STATUSES
        and app.next_step_at is not None
        and app.next_step_at <= now
    ]


def _weekly_plan(
    *,
    resumes: list[Resume],
    versions: list[ResumeVersion],
    applications: list[ApplicationRecord],
    proof_assets: list[ProofAsset],
    interviews: list[InterviewSession],
    runway: RunwaySnapshot | None,
) -> list[str]:
    due = _due_applications(applications)
    active_apps = [a for a in applications if a.status in ACTIVE_APPLICATION_STATUSES]
    ready_proof = [p for p in proof_assets if p.status in {"ready", "approved"}]
    completed_interviews = [i for i in interviews if i.status == "completed"]
    plan: list[str] = []
    if not runway:
        plan.append("Create a runway snapshot so weekly planning uses your real cash assumptions.")
    if not resumes:
        plan.append("Upload your source resume before JD matching or campaign generation.")
    elif not versions:
        plan.append("Create one targeted resume version for your highest-priority role.")
    if due:
        plan.append(f"Resolve {len(due)} due application follow-up item(s).")
    if len(active_apps) < 5:
        plan.append("Add enough target roles to maintain a healthy weekly pipeline.")
    if len(ready_proof) < 2:
        plan.append("Promote at least two proof assets to ready or approved with citations.")
    if not completed_interviews:
        plan.append("Complete one interview practice session and record a score.")
    return plan[:5]


def _reminder_dict(
    *,
    reminder_id: str,
    title: str,
    detail: str,
    due_at: datetime | None,
    source_type: str,
    source_id: str,
    severity: str,
    href: str,
) -> dict[str, Any]:
    return {
        "id": reminder_id,
        "title": title,
        "detail": detail,
        "due_at": due_at,
        "source_type": source_type,
        "source_id": source_id,
        "severity": severity,
        "href": href,
        "delivery": "in_app",
    }


def build_reminders(
    *,
    applications: list[ApplicationRecord],
    interviews: list[InterviewSession],
    runway: RunwaySnapshot | None,
) -> list[dict[str, Any]]:
    now = _now()
    upcoming_window = now + timedelta(days=7)
    reminders: list[dict[str, Any]] = []
    for app in applications:
        if app.status not in ACTIVE_APPLICATION_STATUSES or not app.next_step_at:
            continue
        if app.next_step_at <= upcoming_window:
            severity = "overdue" if app.next_step_at < now else "due"
            reminders.append(
                _reminder_dict(
                    reminder_id=f"application:{app.id}:next_step",
                    title=f"{app.company}: {app.next_step or 'Follow up'}",
                    detail=f"{app.role} is in {app.status.replace('_', ' ')}.",
                    due_at=app.next_step_at,
                    source_type="application",
                    source_id=app.id,
                    severity=severity,
                    href="/applications",
                )
            )
    for session in interviews:
        if session.status not in {"planned", "scheduled"} or not session.scheduled_at:
            continue
        if session.scheduled_at <= upcoming_window:
            reminders.append(
                _reminder_dict(
                    reminder_id=f"interview:{session.id}:scheduled",
                    title=f"{session.target_role} interview practice",
                    detail=session.company or "Practice session scheduled.",
                    due_at=session.scheduled_at,
                    source_type="interview",
                    source_id=session.id,
                    severity="due" if session.scheduled_at >= now else "overdue",
                    href="/interview",
                )
            )
    months = _runway_months(runway)
    if runway and months is not None and months < 4:
        reminders.append(
            _reminder_dict(
                reminder_id=f"runway:{runway.id}:risk",
                title="Runway risk review",
                detail=f"Current snapshot estimates {months} months of runway.",
                due_at=None,
                source_type="runway",
                source_id=runway.id,
                severity="risk",
                href="/runway",
            )
        )
    return sorted(reminders, key=lambda r: r["due_at"] or now)


async def dashboard_summary(db: AsyncSession, user_id: str) -> dict[str, Any]:
    runway = list(
        (
            await db.execute(
                select(RunwaySnapshot)
                .where(RunwaySnapshot.user_id == user_id, RunwaySnapshot.deleted_at.is_(None))
                .order_by(RunwaySnapshot.updated_at.desc(), RunwaySnapshot.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    applications = list(
        (
            await db.execute(
                select(ApplicationRecord)
                .where(ApplicationRecord.user_id == user_id, ApplicationRecord.deleted_at.is_(None))
                .order_by(ApplicationRecord.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    proof_assets = list(
        (
            await db.execute(
                select(ProofAsset)
                .where(ProofAsset.user_id == user_id, ProofAsset.deleted_at.is_(None))
                .order_by(ProofAsset.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    interviews = list(
        (
            await db.execute(
                select(InterviewSession)
                .where(InterviewSession.user_id == user_id, InterviewSession.deleted_at.is_(None))
                .order_by(InterviewSession.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    resumes = list(
        (
            await db.execute(
                select(Resume)
                .where(Resume.user_id == user_id, Resume.deleted_at.is_(None))
                .order_by(Resume.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    versions = list(
        (
            await db.execute(
                select(ResumeVersion)
                .where(ResumeVersion.user_id == user_id, ResumeVersion.deleted_at.is_(None))
                .order_by(ResumeVersion.created_at.desc())
            )
        )
        .scalars()
        .all()
    )

    latest_runway = _latest(runway)
    months = _runway_months(latest_runway)
    active_apps = [a for a in applications if a.status in ACTIVE_APPLICATION_STATUSES]
    due_apps = _due_applications(applications)
    interview_apps = [a for a in applications if a.status in INTERVIEW_APPLICATION_STATUSES]
    scored_apps = [a.fit_score for a in applications if a.fit_score is not None]
    avg_fit = round(sum(scored_apps) / len(scored_apps)) if scored_apps else 0
    interview_scores = [i.score for i in interviews if i.score is not None]
    avg_interview = (
        round(sum(interview_scores) / len(interview_scores)) if interview_scores else 0
    )
    ready_proof = [p for p in proof_assets if p.status in {"ready", "approved"}]
    completed_interviews = [i for i in interviews if i.status == "completed"]
    readiness = _readiness(
        resumes=resumes,
        versions=versions,
        applications=applications,
        proof_assets=proof_assets,
        interviews=interviews,
        runway_months=months,
    )

    reminders = build_reminders(
        applications=applications, interviews=interviews, runway=latest_runway
    )
    return {
        "readiness_score": readiness,
        "readiness_note": "Real user data, not demo metrics.",
        "metrics": {
            "runway_months": months,
            "runway_risk": _runway_risk(months),
            "active_applications": len(active_apps),
            "followups_due": len(due_apps),
            "average_fit_score": avg_fit,
            "interview_stage_applications": len(interview_apps),
            "resume_count": len(resumes),
            "resume_version_count": len(versions),
            "proof_ready_count": len(ready_proof),
            "proof_total_count": len(proof_assets),
            "interview_completed_count": len(completed_interviews),
            "interview_average_score": avg_interview,
        },
        "weekly_plan": _weekly_plan(
            resumes=resumes,
            versions=versions,
            applications=applications,
            proof_assets=proof_assets,
            interviews=interviews,
            runway=latest_runway,
        ),
        "reminders": reminders[:8],
        "safety_posture": {
            "deterministic_services": True,
            "human_approval_required": True,
            "external_actions_disabled": True,
        },
    }
