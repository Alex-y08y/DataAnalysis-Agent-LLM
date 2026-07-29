from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.user import User
from models.analysis_task import AnalysisTask, TaskStatus
from api.auth_api import get_current_user
from utils.db_utils import get_db

router = APIRouter(prefix="/api/reports", tags=["reports"])


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------
class TemplateOut(BaseModel):
    id: int
    name: str
    config: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplateCreate(BaseModel):
    name: str
    config: dict[str, Any]


class GenerateRequest(BaseModel):
    template_id: int | None = None
    task_ids: list[int]
    title: str = "Auto Report"
    format: str = "pdf"  # pdf / html / xlsx


class ScheduleOut(BaseModel):
    id: int
    name: str
    cron: str
    config: str | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduleCreate(BaseModel):
    name: str
    cron: str
    config: dict[str, Any] | None = None


# --------------------------------------------------------------------------
# Stub table for templates & schedules (in memory until a real table is added)
# --------------------------------------------------------------------------
_templates: list[dict[str, Any]] = []
_template_id_counter = 0
_schedules: list[dict[str, Any]] = []
_schedule_id_counter = 0


# --------------------------------------------------------------------------
# Templates CRUD
# --------------------------------------------------------------------------
@router.get("/templates", response_model=list[TemplateOut])
def list_templates(_user: User = Depends(get_current_user)):
    return _templates


@router.post("/templates", response_model=TemplateOut, status_code=201)
def create_template(body: TemplateCreate, _user: User = Depends(get_current_user)):
    global _template_id_counter
    _template_id_counter += 1
    tpl = {
        "id": _template_id_counter,
        "name": body.name,
        "config": str(body.config),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    _templates.append(tpl)
    return tpl


@router.delete("/templates/{tpl_id}", status_code=204)
def delete_template(tpl_id: int, _user: User = Depends(get_current_user)):
    global _templates
    _templates = [t for t in _templates if t["id"] != tpl_id]


# --------------------------------------------------------------------------
# Generate
# --------------------------------------------------------------------------
@router.post("/generate")
def generate_report(
    body: GenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tasks = (
        db.query(AnalysisTask)
        .filter(AnalysisTask.id.in_(body.task_ids), AnalysisTask.user_id == current_user.id)
        .all()
    )
    if not tasks:
        raise HTTPException(status_code=404, detail="No valid tasks found")
    # TODO: assemble report from tasks
    return {"message": f"Report '{body.title}' generated", "task_count": len(tasks)}


@router.get("/export/{report_id}")
def export_report(report_id: int, _user: User = Depends(get_current_user)):
    # TODO: return actual file
    return {"message": f"Export placeholder for report {report_id}"}


# --------------------------------------------------------------------------
# Schedules
# --------------------------------------------------------------------------
@router.get("/schedules", response_model=list[ScheduleOut])
def list_schedules(_user: User = Depends(get_current_user)):
    return _schedules


@router.post("/schedules", response_model=ScheduleOut, status_code=201)
def create_schedule(body: ScheduleCreate, _user: User = Depends(get_current_user)):
    global _schedule_id_counter
    _schedule_id_counter += 1
    sch = {
        "id": _schedule_id_counter,
        "name": body.name,
        "cron": body.cron,
        "config": str(body.config) if body.config else None,
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    _schedules.append(sch)
    return sch


@router.put("/schedules/{sch_id}/toggle")
def toggle_schedule(sch_id: int, _user: User = Depends(get_current_user)):
    for sch in _schedules:
        if sch["id"] == sch_id:
            sch["is_active"] = not sch["is_active"]
            return sch
    raise HTTPException(status_code=404, detail="Schedule not found")


@router.delete("/schedules/{sch_id}", status_code=204)
def delete_schedule(sch_id: int, _user: User = Depends(get_current_user)):
    global _schedules
    _schedules = [s for s in _schedules if s["id"] != sch_id]
