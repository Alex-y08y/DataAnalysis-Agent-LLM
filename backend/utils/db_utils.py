import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from models.user import Base as UserBase

# --------------------------------------------------------------------------
# Database URL (override via environment variable)
# --------------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data_analysis.db",
)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables defined by models that share the same Base."""
    from models.datasource import Base as DSBase
    from models.analysis_task import Base as ATBase
    from models.audit_log import Base as ALBase
    from models.knowledge_document import Base as KDBase

    UserBase.metadata.create_all(bind=engine)
    DSBase.metadata.create_all(bind=engine)
    ATBase.metadata.create_all(bind=engine)
    ALBase.metadata.create_all(bind=engine)
    KDBase.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
