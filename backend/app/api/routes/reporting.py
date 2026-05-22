from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import DbSession, get_current_user
from app.models.block_attempt import BlockAttempt
from app.models.user import User
from app.schemas.reporting import WeeklyReportResponse

router = APIRouter()


@router.get("/weekly-report", response_model=WeeklyReportResponse)
async def weekly_report(db: DbSession, current_user: User = Depends(get_current_user)) -> WeeklyReportResponse:
    result = await db.execute(select(BlockAttempt.domain).where(BlockAttempt.user_id == current_user.id))
    domains = [row[0] for row in result.all()]
    total_attempts = len(domains)
    most_attempted = Counter(domains).most_common(1)
    most_attempted_domain = most_attempted[0][0] if most_attempted else None
    focus_score = round(max(0.0, 100.0 - min(90.0, total_attempts * 9.0)), 2)
    return WeeklyReportResponse(
        user_id=str(current_user.id),
        attempts=total_attempts,
        most_attempted_website=most_attempted_domain,
        focus_score=focus_score,
        unique_domains=len(set(domains)),
    )
