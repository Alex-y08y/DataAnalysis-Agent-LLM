import re
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

# --------------------------------------------------------------------------
# Password utilities (re-exported from auth_service for convenience)
# --------------------------------------------------------------------------
_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


# --------------------------------------------------------------------------
# JWT utilities
# --------------------------------------------------------------------------
SECRET_KEY = "change-me-to-a-secure-random-string"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# --------------------------------------------------------------------------
# SQL injection detection (basic heuristics)
# --------------------------------------------------------------------------
_SQL_INJECTION_PATTERNS = [
    re.compile(r"\bDROP\s+TABLE", re.IGNORECASE),
    re.compile(r"\bDROP\s+DATABASE", re.IGNORECASE),
    re.compile(r"\bTRUNCATE\s+TABLE", re.IGNORECASE),
    re.compile(r"\bALTER\s+TABLE", re.IGNORECASE),
    re.compile(r"\bALTER\s+DATABASE", re.IGNORECASE),
    re.compile(r"--\s*$"),                          # comment injection
    re.compile(r";\s*$"),                           # stacked query injection
]


def has_sql_injection(text: str) -> bool:
    """Return True if the text contains patterns typical of SQL injection."""
    for pattern in _SQL_INJECTION_PATTERNS:
        if pattern.search(text):
            return True
    return False
