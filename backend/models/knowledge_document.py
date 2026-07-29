from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum
from sqlalchemy.orm import declarative_base

import enum

Base = declarative_base()


class DocStatus(str, enum.Enum):
    uploading = "uploading"
    ready = "ready"
    failed = "failed"


class DocType(str, enum.Enum):
    pdf = "pdf"
    txt = "txt"
    md = "md"
    excel = "excel"


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(256), nullable=False)
    doc_type = Column(SAEnum(DocType), nullable=False)
    file_path = Column(String(512), nullable=True)
    content_summary = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0, nullable=False)
    metadata_tags = Column(Text, nullable=True)            # JSON string
    status = Column(SAEnum(DocStatus), default=DocStatus.uploading, nullable=False)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<KnowledgeDocument(id={self.id}, title={self.title!r}, type={self.doc_type.value})>"
