from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, get_current_user
from app.models.block_attempt import BlockAttempt
from app.models.blocked_site import BlockedSite
from app.models.friend import Friend
from app.models.user import User
from app.schemas.blocking import AttemptLogRequest, BlockedSiteCreate, BlockedSiteRead, RemoveBlockedSiteRequest
from app.services.notifications import notify_friend_about_block

router = APIRouter()


def normalize_domain(domain: str) -> str:
    return domain.strip().lower().removeprefix("www.")


@router.post("/add-blocked-site", response_model=BlockedSiteRead)
async def add_blocked_site(payload: BlockedSiteCreate, db: DbSession, current_user: User = Depends(get_current_user)) -> BlockedSiteRead | BlockedSite:
    normalized_domain = normalize_domain(payload.domain)
    result = await db.execute(
        select(BlockedSite).where(BlockedSite.user_id == current_user.id, BlockedSite.domain == normalized_domain)
    )
    existing_site = result.scalar_one_or_none()
    if existing_site is not None:
        return existing_site

    site = BlockedSite(user_id=current_user.id, domain=normalized_domain)
    db.add(site)
    await db.commit()
    await db.refresh(site)
    return site


@router.post("/remove-blocked-site")
async def remove_blocked_site(payload: RemoveBlockedSiteRequest, db: DbSession, current_user: User = Depends(get_current_user)) -> dict[str, str]:
    result = await db.execute(select(BlockedSite).where(BlockedSite.user_id == current_user.id, BlockedSite.domain == normalize_domain(payload.domain)))
    site = result.scalar_one_or_none()
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blocked site not found")
    await db.delete(site)
    await db.commit()
    return {"status": "removed"}


@router.post("/log-attempt")
async def log_attempt(payload: AttemptLogRequest, db: DbSession, current_user: User = Depends(get_current_user)) -> dict[str, str]:
    attempt = BlockAttempt(
        user_id=current_user.id,
        domain=normalize_domain(payload.domain),
        metadata_json=payload.model_dump_json(),
        source=payload.source,
    )
    db.add(attempt)
    await db.commit()

    result = await db.execute(select(Friend).where(Friend.user_id == current_user.id).order_by(Friend.created_at.desc()).limit(1))
    friend = result.scalar_one_or_none()
    if friend:
        await notify_friend_about_block(db=db, user=current_user, friend=friend, domain=attempt.domain)
    return {"status": "logged"}
