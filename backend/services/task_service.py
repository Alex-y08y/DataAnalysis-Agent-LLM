import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.analysis_task import AnalysisTask, TaskStatus

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError:
    BackgroundScheduler = None


class TaskService:
    """Manage analysis-task lifecycle."""

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @staticmethod
    def get_all(
        db: Session, user_id: Optional[int] = None,
        skip: int = 0, limit: int = 50,
    ) -> List[AnalysisTask]:
        q = db.query(AnalysisTask)
        if user_id is not None:
            q = q.filter(AnalysisTask.user_id == user_id)
        return q.order_by(AnalysisTask.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, task_id: int) -> Optional[AnalysisTask]:
        return db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()

    @staticmethod
    def create(db: Session, data: Dict[str, Any]) -> AnalysisTask:
        task = AnalysisTask(**data)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def update_status(
        db: Session, task_id: int, status: TaskStatus,
        error_message: Optional[str] = None, **extra,
    ) -> Optional[AnalysisTask]:
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if not task:
            return None
        task.status = status
        if status == TaskStatus.running:
            task.started_at = datetime.utcnow()
        elif status in (TaskStatus.completed, TaskStatus.failed):
            task.completed_at = datetime.utcnow()
        if error_message:
            task.error_message = error_message
        for k, v in extra.items():
            if hasattr(task, k):
                setattr(task, k, v)
        db.commit()
        db.refresh(task)
        return task

    # ------------------------------------------------------------------
    # Copy / reuse
    # ------------------------------------------------------------------
    @staticmethod
    def copy_task(db: Session, task_id: int) -> Optional[AnalysisTask]:
        original = TaskService.get_by_id(db, task_id)
        if not original:
            return None
        new_task = AnalysisTask(
            user_id=original.user_id,
            title=f"[Copy] {original.title or ''}",
            question_text=original.question_text,
            intent_type=original.intent_type,
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        return new_task

    # ------------------------------------------------------------------
    # Batch analysis
    # ------------------------------------------------------------------
    @staticmethod
    def batch_create(db: Session, tasks_data: List[Dict[str, Any]]) -> List[AnalysisTask]:
        tasks = [AnalysisTask(**d) for d in tasks_data]
        for t in tasks:
            db.add(t)
        db.commit()
        for t in tasks:
            db.refresh(t)
        return tasks

    # ------------------------------------------------------------------
    # Retry failed
    # ------------------------------------------------------------------
    @staticmethod
    def retry_failed(db: Session, task_id: int) -> Optional[AnalysisTask]:
        task = TaskService.get_by_id(db, task_id)
        if not task or task.status != TaskStatus.failed:
            return None
        task.status = TaskStatus.pending
        task.error_message = None
        task.started_at = None
        task.completed_at = None
        db.commit()
        db.refresh(task)
        return task

    # ------------------------------------------------------------------
    # Scheduler helpers (APScheduler)
    # ------------------------------------------------------------------
    _scheduler = None

    @classmethod
    def start_scheduler(cls):
        if BackgroundScheduler is None:
            return
        if cls._scheduler is None or not cls._scheduler.running:
            cls._scheduler = BackgroundScheduler()
            cls._scheduler.start()

    @classmethod
    def stop_scheduler(cls):
        if cls._scheduler and cls._scheduler.running:
            cls._scheduler.shutdown(wait=False)
            cls._scheduler = None

    @classmethod
    def schedule_task(
        cls,
        func,
        trigger: str = "interval",
        hours: int = 0,
        minutes: int = 0,
        **kwargs,
    ):
        cls.start_scheduler()
        cls._scheduler.add_job(func, trigger, **{"hours": hours, "minutes": minutes, **kwargs})
