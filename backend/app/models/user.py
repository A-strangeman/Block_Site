from __future__ import annotations

from datetime import datetime
from typing import List, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.blocked_site import BlockedSite
    from app.models.friend import Friend
    from app.models.block_attempt import BlockAttempt
    from app.models.approval_request import ApprovalRequest


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    blocked_sites: Mapped[List["BlockedSite"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    friends: Mapped[List["Friend"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    block_attempts: Mapped[List["BlockAttempt"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    approval_requests: Mapped[List["ApprovalRequest"]] = relationship(back_populates="user", cascade="all, delete-orphan")
