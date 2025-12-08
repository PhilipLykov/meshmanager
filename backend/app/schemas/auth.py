"""Schemas for authentication."""

from pydantic import BaseModel


class UserInfo(BaseModel):
    """Current user information."""

    id: str
    email: str | None = None
    display_name: str | None = None
    is_admin: bool = False

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """OAuth token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int | None = None


class AuthStatus(BaseModel):
    """Authentication status response."""

    authenticated: bool
    user: UserInfo | None = None
    oidc_enabled: bool = False
