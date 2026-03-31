from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


# ── Auth schemas ──────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    expires_in: int = 3600  # seconds


class LogoutResponse(BaseModel):
    message: str


# ── User management schemas ───────────────────────────────────────────────────
VALID_SUFFIXES = (
    "@analyst.quantrisk",
    "@portviewer.quantrisk",
    "@dbadmin.quantrisk",
)


class UserCreate(BaseModel):
    username: str
    email: str
    password: str = Field(min_length=8, description="Minimum 8 characters")
    full_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username_format(cls, v: str) -> str:
        if not any(v.lower().endswith(s) for s in VALID_SUFFIXES):
            raise ValueError(
                "username must end with @analyst.quantrisk, "
                "@portviewer.quantrisk, or @dbadmin.quantrisk"
            )
        local = v.split("@")[0]
        if not local or len(local) < 2:
            raise ValueError("Username local part must be at least 2 characters")
        return v.lower()


class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    bio: Optional[str] = None


class UserProfileResponse(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    role: str           # derived from username at response time
    is_active: bool
    created_at: Optional[datetime] = None
    profile: Optional[UserProfileResponse] = None

    class Config:
        from_attributes = True


class MeResponse(BaseModel):
    user_id: int
    username: str
    email: str
    role: str
    is_active: bool
