from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.auth import hash_password, extract_role, require_role
from models.user import User, UserProfile
from schemas.auth import UserCreate, UserUpdate, UserResponse

router = APIRouter()

# All routes in this module are ADMIN-only
AdminOnly = Depends(require_role("ADMIN"))


def _derive_role(username: str) -> str:
    try:
        return extract_role(username)
    except Exception:
        return "UNKNOWN"


def _to_response(user: User) -> UserResponse:
    return UserResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        role=_derive_role(user.username),
        is_active=user.is_active,
        created_at=user.created_at,
        profile=user.profile,
    )


@router.get("/", response_model=List[UserResponse], dependencies=[AdminOnly])
def list_users(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List all users (paginated). ADMIN only."""
    users = db.query(User).offset(skip).limit(limit).all()
    return [_to_response(u) for u in users]


@router.get("/{user_id}", response_model=UserResponse, dependencies=[AdminOnly])
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a single user by ID. ADMIN only."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_response(user)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[AdminOnly])
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user. Username must follow the domain format.
    Password is bcrypt-hashed before storage. ADMIN only.
    """
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="Username already exists")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already in use")

    new_user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(new_user)
    db.flush()

    if payload.full_name:
        profile = UserProfile(user_id=new_user.user_id, full_name=payload.full_name)
        db.add(profile)

    db.commit()
    db.refresh(new_user)
    return _to_response(new_user)


@router.put("/{user_id}", response_model=UserResponse, dependencies=[AdminOnly])
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    """
    Update user info. Optionally reset password (will be re-hashed).
    Soft-disable via is_active=False. ADMIN only.
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.email is not None:
        existing = db.query(User).filter(User.email == payload.email, User.user_id != user_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use by another user")
        user.email = payload.email

    if payload.password is not None:
        user.password_hash = hash_password(payload.password)

    if payload.is_active is not None:
        user.is_active = payload.is_active

    # Profile fields
    profile_updates = {k: v for k, v in {
        "full_name": payload.full_name,
        "phone": payload.phone,
        "department": payload.department,
        "bio": payload.bio,
    }.items() if v is not None}

    if profile_updates:
        if user.profile:
            for k, v in profile_updates.items():
                setattr(user.profile, k, v)
        else:
            profile = UserProfile(user_id=user_id, **profile_updates)
            db.add(profile)

    db.commit()
    db.refresh(user)
    return _to_response(user)


@router.delete("/{user_id}", dependencies=[AdminOnly])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Soft-delete a user (sets is_active=False). ADMIN only.
    Hard deletion is intentionally avoided to preserve audit trail.
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    return {"message": f"User '{user.username}' deactivated successfully."}
