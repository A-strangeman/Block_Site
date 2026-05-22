from pydantic import BaseModel


class WeeklyReportResponse(BaseModel):
    user_id: str
    attempts: int
    most_attempted_website: str | None
    focus_score: float
    unique_domains: int
