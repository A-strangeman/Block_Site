from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from app.api.deps import DbSession, get_current_user
from app.models.approval_request import ApprovalRequest
from app.models.friend import Friend
from app.models.user import User
from app.schemas.accountability import ApprovalDecision, ApprovalRequestCreate, ApprovalRequestRead, FriendCreate, FriendRead
from app.services.notifications import send_approval_request_notification

router = APIRouter()


@router.post("/send-approval", response_model=ApprovalRequestRead)
async def send_approval(payload: ApprovalRequestCreate, db: DbSession, current_user: User = Depends(get_current_user)) -> ApprovalRequestRead | ApprovalRequest:
    token = token_urlsafe(32)
    request = ApprovalRequest(
        user_id=current_user.id,
        status="pending",
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)

    result = await db.execute(select(Friend).where(Friend.user_id == current_user.id).order_by(Friend.created_at.desc()).limit(1))
    friend = result.scalar_one_or_none()
    if friend:
        await send_approval_request_notification(db=db, user=current_user, friend=friend, request=request)
    return request


@router.post("/approve-access")
async def approve_access(payload: ApprovalDecision, db: DbSession) -> dict[str, Any]:
    result = await db.execute(select(ApprovalRequest).where(ApprovalRequest.token == payload.token))
    request = result.scalar_one_or_none()
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")
    expires_at = request.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        request.status = "expired"
        await db.commit()
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Approval request expired")

    request.status = "approved"
    request.approved_at = datetime.now(timezone.utc)
    request.approved_by = payload.approver
    await db.commit()
    return {"status": "approved", "unlock_minutes": 5}


@router.get("/approve", response_class=HTMLResponse)
async def approve_via_link(token: str, db: DbSession) -> str:
    result = await db.execute(select(ApprovalRequest).where(ApprovalRequest.token == token))
    request = result.scalar_one_or_none()
    if request is None:
        return "<html><body><h1>Error</h1><p>Approval request not found or invalid.</p></body></html>"
    expires_at = request.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        request.status = "expired"
        await db.commit()
        return "<html><body><h1>Error</h1><p>Approval request has expired.</p></body></html>"

    request.status = "approved"
    request.approved_at = datetime.now(timezone.utc)
    request.approved_by = "link"
    await db.commit()
    return "<html><body><h1>Access Approved</h1><p>You approved access for the requester. They will be temporarily unlocked for 5 minutes.</p></body></html>"


@router.post("/add-friend", response_model=FriendRead)
async def add_friend(payload: FriendCreate, db: DbSession, current_user: User = Depends(get_current_user)) -> FriendRead | Friend:
    friend = Friend(
        user_id=current_user.id,
        name=payload.name,
        email=payload.email.lower() if payload.email else None,
        phone=payload.phone,
        notification_channel=payload.notification_channel,
    )
    db.add(friend)
    await db.commit()
    await db.refresh(friend)
    return friend
