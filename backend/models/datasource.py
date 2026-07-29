from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum
from sqlalchemy.orm import declarative_base

import enum

Base = declarative_base()


class DataSourceType(str, enum.Enum):
    mysql = "mysql"
    hive = "hive"
    csv = "csv"
    api = "api"


class DataSource(Base):
    __tablename__ = "datasources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, index=True)
    type = Column(SAEnum(DataSourceType), nullable=False)
    host = Column(String(256), nullable=True)
    port = Column(Integer, nullable=True)
    user = Column(String(128), nullable=True)
    password_encrypted = Column(String(512), nullable=True)
    database_name = Column(String(128), nullable=True)
    extra_config = Column(Text, nullable=True)               # JSON string
    bind_roles = Column(String(256), nullable=True)          # comma-separated roles
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<DataSource(id={self.id}, name={self.name!r}, type={self.type.value})>"
