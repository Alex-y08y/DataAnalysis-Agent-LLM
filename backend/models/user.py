from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import declarative_base

import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    admin = "admin"
    analyst = "analyst"
    operator = "operator"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    email = Column(String(128), unique=True, nullable=True)
    role = Column(SAEnum(UserRole), default=UserRole.analyst, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username!r}, role={self.role.value})>"
