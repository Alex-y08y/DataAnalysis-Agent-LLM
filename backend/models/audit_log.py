from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True, index=True)
    action_type = Column(String(64), nullable=False, index=True)
    question_text = Column(Text, nullable=True)
    sql_executed = Column(Text, nullable=True)
    tool_calls = Column(Text, nullable=True)               # JSON string
    file_exported = Column(String(512), nullable=True)
    ip_address = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action_type={self.action_type!r}, user_id={self.user_id})>"
