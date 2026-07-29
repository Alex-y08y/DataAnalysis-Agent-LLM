from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.user import User
from models.analysis_task import AnalysisTask
from api.auth_api import get_current_user
from utils.db_utils import get_db

router = APIRouter(prefix="/api/chat", tags=["chat"])


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------
class SendMessageRequest(BaseModel):
    question: str
    datasource_id: int | None = None


class MessageResponse(BaseModel):
    task_id: int
    answer: str
    sql: str | None = None
    chart_config: dict[str, Any] | None = None


class TaskListItem(BaseModel):
    id: int
    title: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@router.post("/send", response_model=MessageResponse)
def send_message(
    body: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a question — the Agent engine will process it synchronously."""
    # TODO: plug in the actual Agent engine here
    task = AnalysisTask(
        user_id=current_user.id,
        question_text=body.question,
        title=body.question[:80],
        status="completed",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return MessageResponse(
        task_id=task.id,
        answer=f"[Stub] Received your question: {body.question}",
        sql=None,
        chart_config=None,
    )


@router.get("/history")
def get_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tasks = (
        db.query(AnalysisTask)
        .filter(AnalysisTask.user_id == current_user.id)
        .order_by(AnalysisTask.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return tasks


@router.get("/tasks", response_model=list[TaskListItem])
def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tasks = (
        db.query(AnalysisTask)
        .filter(AnalysisTask.user_id == current_user.id)
        .order_by(AnalysisTask.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return tasks


# --------------------------------------------------------------------------
# WebSocket real-time chat
# --------------------------------------------------------------------------
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # TODO: route to Agent engine stream
            await websocket.send_text(f"[Echo] {data}")
    except WebSocketDisconnect:
        pass
