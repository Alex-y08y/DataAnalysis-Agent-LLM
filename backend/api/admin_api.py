from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.user import User, UserRole
from models.audit_log import AuditLog
from models.analysis_task import AnalysisTask
from api.auth_api import get_current_user
from utils.db_utils import get_db
from services.auth_service import AuthService

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


# --------------------------------------------------------------------------
# User management
# --------------------------------------------------------------------------
class UserOut(BaseModel):
    id: int
    username: str
    email: str | None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RoleUpdate(BaseModel):
    role: UserRole


@router.get("/users", response_model=list[UserOut])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    return db.query(User).offset(skip).limit(limit).all()


@router.put("/users/{user_id}/role", response_model=UserOut)
def update_role(
    user_id: int,
    body: RoleUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = body.role
    db.commit()
    db.refresh(user)
    return user


# --------------------------------------------------------------------------
# Audit logs
# --------------------------------------------------------------------------
class AuditLogOut(BaseModel):
    id: int
    user_id: int | None
    action_type: str
    question_text: str | None
    sql_executed: str | None
    tool_calls: str | None
    ip_address: str | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/logs", response_model=list[AuditLogOut])
def list_logs(
    action_type: str | None = Query(None),
    user_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    q = db.query(AuditLog)
    if action_type:
        q = q.filter(AuditLog.action_type == action_type)
    if user_id is not None:
        q = q.filter(AuditLog.user_id == user_id)
    return q.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()


# --------------------------------------------------------------------------
# System stats
# --------------------------------------------------------------------------
class SystemStats(BaseModel):
    total_users: int
    total_tasks: int
    total_logs: int
    tasks_by_status: dict[str, int]


@router.get("/stats", response_model=SystemStats)
def system_stats(
    db: Session = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_tasks = db.query(func.count(AnalysisTask.id)).scalar() or 0
    total_logs = db.query(func.count(AuditLog.id)).scalar() or 0

    status_counts = (
        db.query(AnalysisTask.status, func.count(AnalysisTask.id))
        .group_by(AnalysisTask.status)
        .all()
    )
    tasks_by_status = {s: c for s, c in status_counts}

    return SystemStats(
        total_users=total_users,
        total_tasks=total_tasks,
        total_logs=total_logs,
        tasks_by_status=tasks_by_status,
    )
