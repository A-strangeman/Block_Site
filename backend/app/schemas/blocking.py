from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BlockedSiteCreate(BaseModel):
    domain: str = Field(min_length=1, max_length=255)


class BlockedSiteRead(BaseModel):
    id: UUID
    domain: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RemoveBlockedSiteRequest(BaseModel):
    domain: str = Field(min_length=1, max_length=255)


class AttemptLogRequest(BaseModel):
    domain: str = Field(min_length=1, max_length=255)
    url: str
    tab_id: int | None = None
    source: str = Field(default="extension", max_length=32)
    reason: str = Field(default="blocked", max_length=64)
