"""Authentication endpoints."""

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse

from app.auth.middleware import get_current_user_optional
from app.config import get_settings
from app.models import User
from app.schemas.auth import AuthStatus, UserInfo

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.get("/status")
async def auth_status(
    user: User | None = Depends(get_current_user_optional),
) -> AuthStatus:
    """Get current authentication status."""
    return AuthStatus(
        authenticated=user is not None,
        user=UserInfo.model_validate(user) if user else None,
        oidc_enabled=settings.oidc_enabled,
    )


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    """Initiate OIDC login flow."""
    if not settings.oidc_enabled:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="OIDC is not configured")

    from app.auth.oidc import get_oauth_client

    oauth = get_oauth_client()
    redirect_uri = settings.oidc_redirect_uri or str(request.url_for("auth_callback"))
    return await oauth.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def auth_callback(request: Request) -> RedirectResponse:
    """Handle OIDC callback."""
    if not settings.oidc_enabled:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="OIDC is not configured")

    from app.auth.oidc import get_oauth_client, process_oidc_callback

    oauth = get_oauth_client()
    token = await oauth.authorize_access_token(request)

    # Process the callback and create/update user
    user = await process_oidc_callback(token)

    # Store user ID in session
    request.session["user_id"] = user.id

    # Redirect to frontend
    return RedirectResponse(url="/", status_code=302)


@router.post("/logout")
async def logout(request: Request, response: Response) -> dict:
    """Log out the current user."""
    request.session.clear()
    return {"message": "Logged out"}
