from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from core.database import get_db
from core.auth import (
    verify_password,
    create_access_token,
    extract_role,
    blacklist_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from models.user import User
from schemas.auth import LoginRequest, TokenResponse, LogoutResponse, MeResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user. Role is determined automatically from the username suffix:
    - `name@analyst.quantrisk`    → ANALYST
    - `name@portviewer.quantrisk` → VIEWER
    - `name@dbadmin.quantrisk`    → ADMIN
    """
    # Validate username format first (raises 400 if bad domain)
    role = extract_role(req.username)

    user = db.query(User).filter(
        User.username == req.username.lower(),
        User.is_active == True
    ).first()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={"sub": user.username, "role": role, "user_id": user.user_id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(
        access_token=token,
        role=role,
        username=user.username,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(current_user: dict = Depends(get_current_user)):
    """
    Terminates the current session by blacklisting this token's JTI.
    Any subsequent request with this token will receive 401.
    """
    blacklist_token(current_user["jti"])
    return LogoutResponse(message=f"Session for '{current_user['username']}' terminated successfully.")


@router.get("/me", response_model=MeResponse)
def get_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns the profile of the currently authenticated user.
    """
    user = db.query(User).filter(User.user_id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return MeResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        role=current_user["role"],
        is_active=user.is_active,
    )
