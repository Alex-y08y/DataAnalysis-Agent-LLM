from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.user import User, UserRole
from services.auth_service import AuthService, create_access_token, decode_token
from utils.db_utils import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str | None = None
    role: UserRole = UserRole.analyst


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    role: str


class UserInfo(BaseModel):
    id: int
    username: str
    email: str | None
    role: str
    is_active: bool

    class Config:
        from_attributes = True


# --------------------------------------------------------------------------
# Dependency: extract & validate JWT
# --------------------------------------------------------------------------
def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(None),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")
    token = authorization[7:]
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = AuthService.get_user_by_id(db, int(user_id))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = AuthService.authenticate_user(db, body.username, body.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        role=user.role.value,
    )


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = AuthService.get_user_by_username(db, body.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    user = AuthService.create_user(db, body.username, body.password, body.email, body.role)
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        role=user.role.value,
    )


@router.get("/me", response_model=UserInfo)
def me(current_user: User = Depends(get_current_user)):
    return current_user
