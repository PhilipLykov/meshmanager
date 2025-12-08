"""User model for OIDC authentication."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """A user authenticated via OIDC."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # OIDC identifiers
    oidc_subject: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    oidc_issuer: Mapped[str] = mapped_column(String(500), nullable=False)

    # User info
    email: Mapped[str | None] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(255))

    # Permissions
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
