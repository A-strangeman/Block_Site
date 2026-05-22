from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class FriendCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    notification_channel: str = Field(default="email", pattern="^(email|sms)$")


class FriendRead(BaseModel):
    id: UUID
    name: str
    email: EmailStr | None
    phone: str | None
    notification_channel: str

    model_config = {"from_attributes": True}


class ApprovalRequestCreate(BaseModel):
    email: EmailStr | None = None
    phone: str | None = None


class ApprovalRequestRead(BaseModel):
    id: UUID
    status: str
    token: str
    expires_at: datetime
    approved_at: datetime | None
    approved_by: str | None

    model_config = {"from_attributes": True}


class ApprovalDecision(BaseModel):
    token: str
    approver: str | None = None
