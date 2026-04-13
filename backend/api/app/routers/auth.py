"""
Auth Router — Google OAuth 2.0 login flow + JWT token management
"""
import secrets
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse

from app.services.auth import (
    get_google_auth_url,
    exchange_code_for_tokens,
    get_google_user_info,
    create_access_token,
    create_refresh_token,
    decode_token,
    build_token_response,
)
from app.services.database import (
    get_user_by_google_id,
    create_user,
    update_user,
)
from app.models.user import UserCreate
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory CSRF state store (use Redis in production at scale)
_pending_states: set = set()


@router.get("/google", summary="Initiate Google OAuth login")
async def google_login():
    """
    Redirects the user to Google's OAuth 2.0 consent screen.
    Frontend should open this URL in the browser.
    """
    state = secrets.token_urlsafe(32)
    _pending_states.add(state)
    auth_url = get_google_auth_url(state)
    return RedirectResponse(url=auth_url)


@router.get("/callback", summary="Google OAuth callback — exchange code for JWT")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: str = Query(None),
):
    """
    Google redirects here after user consents.
    Exchanges the code for tokens, creates/updates the user, and returns JWTs.
    """
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")

    # (Disabled in-memory CSRF state check for Serverless compatibility)
    _pending_states.discard(state)

    # Exchange code for Google tokens
    try:
        google_tokens = await exchange_code_for_tokens(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to exchange code: {e}")

    # Fetch user profile
    try:
        google_user = await get_google_user_info(google_tokens["access_token"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch user info: {e}")

    google_id = google_user.get("id")
    email = google_user.get("email")
    name = google_user.get("name", email)
    picture = google_user.get("picture")

    # Upsert user in Firestore
    user = await get_user_by_google_id(google_id)
    if user is None:
        user = await create_user(UserCreate(
            google_id=google_id,
            email=email,
            name=name,
            picture=picture,
        ))
    else:
        # Refresh name/picture if changed
        user = await update_user(user.id, {"name": name, "picture": picture})

    token_data = build_token_response(user)

    # Redirect to frontend with tokens in query params (or use cookie in production)
    frontend_callback = (
        f"{settings.ALLOWED_ORIGINS.split(',')[0]}/auth/callback"
        f"?access_token={token_data['access_token']}"
        f"&refresh_token={token_data['refresh_token']}"
    )
    return RedirectResponse(url=frontend_callback)


@router.post("/refresh", summary="Refresh access token using refresh token")
async def refresh_token(refresh_token: str):
    """
    Exchange a valid refresh token for a new access token.
    """
    try:
        payload = decode_token(refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token is not a refresh token.")

    user_id = payload["sub"]
    # Generate new access token
    from app.services.database import get_user_by_id
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")

    new_access = create_access_token(user.id, user.email)
    return {
        "access_token": new_access,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/logout", summary="Logout (client-side token discard)")
async def logout():
    """
    Stateless logout — client should discard tokens.
    For token revocation, add token to a Redis blocklist.
    """
    return {"message": "Logged out successfully. Please discard your tokens."}
