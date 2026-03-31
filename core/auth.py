from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from core.database import get_db

# ── Config ──────────────────────────────────────────────────────────────────
SECRET_KEY = "quantrisk-super-secret-jwt-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ── Password hashing ─────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ── Role extraction from username ─────────────────────────────────────────────
ROLE_DOMAINS = {
    "@analyst.quantrisk":   "ANALYST",
    "@portviewer.quantrisk": "VIEWER",
    "@dbadmin.quantrisk":   "ADMIN",
}

def extract_role(username: str) -> str:
    for suffix, role in ROLE_DOMAINS.items():
        if username.lower().endswith(suffix):
            return role
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            "Username must end with one of: "
            "@analyst.quantrisk | @portviewer.quantrisk | @dbadmin.quantrisk"
        ),
    )

# ── Token blacklist (in-memory; swap for Redis in production) ─────────────────
_blacklisted_jtis: set[str] = set()

def blacklist_token(jti: str) -> None:
    _blacklisted_jtis.add(jti)

def is_blacklisted(jti: str) -> bool:
    return jti in _blacklisted_jtis

# ── JWT creation ──────────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload.update({"exp": expire, "jti": str(uuid4())})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# ── Bearer token extraction ───────────────────────────────────────────────────
bearer_scheme = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti: str = payload.get("jti")
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if not username or not jti or not role:
            raise credentials_exc
        if is_blacklisted(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been invalidated. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise credentials_exc

    from models.user import User
    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    if not user:
        raise credentials_exc

    return {"user_id": user.user_id, "username": username, "role": role, "jti": jti}

# ── Role guards ───────────────────────────────────────────────────────────────
def require_role(*allowed_roles: str):
    """
    Returns a FastAPI dependency that enforces role membership.
    Usage: Depends(require_role("ADMIN", "ANALYST"))
    """
    def _guard(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(allowed_roles)}",
            )
        return current_user
    return _guard
