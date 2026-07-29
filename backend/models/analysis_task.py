from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum
from sqlalchemy.orm import declarative_base

import enum

Base = declarative_base()


class TaskStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String(256), nullable=True)
    question_text = Column(Text, nullable=False)
    intent_type = Column(String(64), nullable=True)
    sql_generated = Column(Text, nullable=True)
    data_result = Column(Text, nullable=True)              # JSON string
    chart_config = Column(Text, nullable=True)             # JSON string
    report_content = Column(Text, nullable=True)
    status = Column(SAEnum(TaskStatus), default=TaskStatus.pending, nullable=False)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AnalysisTask(id={self.id}, title={self.title!r}, status={self.status.value})>"
