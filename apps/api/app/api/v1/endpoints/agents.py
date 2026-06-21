from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.agents import (
    ApprovalDecisionRequest,
    ApprovalOut,
    CampaignCreateRequest,
    CampaignOut,
    CampaignRunOut,
    CampaignRunRequest,
)
from app.services.agents import (
    create_campaign,
    decide_approval,
    get_campaign,
    list_approvals,
    list_campaigns,
    run_campaign,
)

router = APIRouter()


@router.post("/campaigns", response_model=CampaignRunOut | CampaignOut)
async def create_agent_campaign(
    payload: CampaignCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    request_id = getattr(request.state, "request_id", None)
    try:
        campaign, run_result = await create_campaign(
            db=db,
            user_id=current_user["id"],
            payload=payload,
            request_id=request_id,
        )
        if run_result:
            return run_result
        return campaign
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/campaigns", response_model=list[CampaignOut])
async def list_agent_campaigns(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await list_campaigns(db, current_user["id"])


@router.get("/campaigns/{campaign_id}", response_model=CampaignOut)
async def get_agent_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    campaign = await get_campaign(db, current_user["id"], campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.post("/campaigns/{campaign_id}/run", response_model=CampaignRunOut)
async def run_agent_campaign(
    campaign_id: str,
    payload: CampaignRunRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    request_id = getattr(request.state, "request_id", None)
    try:
        return await run_campaign(
            db=db,
            user_id=current_user["id"],
            campaign_id=campaign_id,
            payload=payload,
            request_id=request_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/campaigns/{campaign_id}/approvals", response_model=list[ApprovalOut])
async def list_campaign_approvals(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await list_approvals(db, current_user["id"], campaign_id=campaign_id)


@router.get("/approvals", response_model=list[ApprovalOut])
async def list_pending_approvals(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await list_approvals(db, current_user["id"])


@router.post("/approvals/{approval_id}/decide", response_model=ApprovalOut)
async def decide_agent_approval(
    approval_id: str,
    payload: ApprovalDecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await decide_approval(
            db=db,
            user_id=current_user["id"],
            approval_id=approval_id,
            status=payload.status,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

