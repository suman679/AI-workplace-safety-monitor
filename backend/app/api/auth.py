import logging
import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_token,
    hash_password,
    password_fingerprint,
    verify_password,
)
from app.database.session import get_db
from app.models.company import Company
from app.models.user import Role, User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserOut,
)
from app.services.audit import write_audit

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger("safevision.auth")

# Same message for unknown email and wrong password, so accounts can't be enumerated.
BAD_CREDENTIALS = "Invalid email or password"


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
        user=UserOut.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    company = Company(name=body.company_name.strip())
    db.add(company)
    db.flush()
    user = User(
        company_id=company.id,
        full_name=body.full_name.strip(),
        email=email,
        hashed_password=hash_password(body.password),
        role=Role.COMPANY_ADMIN,
    )
    db.add(user)
    db.commit()
    write_audit(db, "REGISTER", request, user.id)
    return _token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.hashed_password):
        write_audit(db, "LOGIN_FAILED", request, user.id if user else None)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, BAD_CREDENTIALS)
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is disabled")
    write_audit(db, "LOGIN", request, user.id)
    return _token_response(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token, "refresh")
        user = db.get(User, uuid.UUID(payload["sub"]))
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication expired")
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication expired")
    return _token_response(user)


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Tokens are stateless; the client discards them. Logout is recorded for auditing.
    write_audit(db, "LOGOUT", request, user.id)
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(body: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user and user.is_active:
        token = create_reset_token(str(user.id), user.hashed_password)
        link = f"{get_settings().FRONTEND_URL}/reset-password?token={token}"
        # Email-ready: swap this log line for an SMTP/provider call later.
        logger.warning("Password reset link for %s: %s", user.email, link)
        write_audit(db, "PASSWORD_RESET_REQUESTED", request, user.id)
    return MessageResponse(message="If that email exists, a reset link has been sent")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(body: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    invalid = HTTPException(status.HTTP_400_BAD_REQUEST, "Reset link is invalid or has expired")
    try:
        payload = decode_token(body.token, "reset")
        user = db.get(User, uuid.UUID(payload["sub"]))
    except (jwt.PyJWTError, ValueError, KeyError):
        raise invalid
    if not user or payload.get("fp") != password_fingerprint(user.hashed_password):
        raise invalid
    user.hashed_password = hash_password(body.new_password)
    db.commit()
    write_audit(db, "PASSWORD_RESET", request, user.id)
    return MessageResponse(message="Password updated. You can now log in.")
