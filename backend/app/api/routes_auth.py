from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import SESSION_COOKIE_NAME, get_current_user, limiter
from app.models.magic_link import MagicLinkToken
from app.models.user import User
from app.schemas.auth import MeOut, RequestLinkIn, RequestLinkOut
from app.security import create_session_jwt, generate_magic_link_token, hash_token
from app.services.email_sender import send_magic_link_email

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session_cookie(response: Response, user_id) -> None:
    token = create_session_jwt(user_id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="none" if settings.cookie_secure else "lax",
        max_age=settings.session_ttl_days * 24 * 3600,
        path="/",
    )


@router.post("/request-link", response_model=RequestLinkOut)
@limiter.limit("5/hour")
def request_link(request: Request, body: RequestLinkIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(email=email)
        db.add(user)
        db.flush()

    raw_token, token_hash, expires_at = generate_magic_link_token()
    db.add(MagicLinkToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
    db.commit()

    link = f"{settings.frontend_origin}/verify?token={raw_token}"
    send_magic_link_email(user.email, link)

    return RequestLinkOut()


@router.get("/verify")
def verify(token: str, db: Session = Depends(get_db)):
    token_hash = hash_token(token)
    record = (
        db.query(MagicLinkToken)
        .filter(MagicLinkToken.token_hash == token_hash)
        .first()
    )
    # SQLite (used in tests) drops tz-awareness on read, unlike Postgres;
    # normalize to aware-UTC here so the comparison is safe on both.
    expires_at = record.expires_at if record else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if (
        record is None
        or record.consumed_at is not None
        or expires_at < datetime.now(UTC)
    ):
        return RedirectResponse(url=f"{settings.frontend_origin}/login?error=invalid_link")

    record.consumed_at = datetime.now(UTC)
    db.commit()

    response = RedirectResponse(url=f"{settings.frontend_origin}/config")
    _set_session_cookie(response, record.user_id)
    return response


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return {"message": "logged out"}
