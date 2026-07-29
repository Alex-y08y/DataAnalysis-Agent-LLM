import json
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.datasource import DataSource, DataSourceType

try:
    import pymysql  # noqa: F401
except ImportError:
    pymysql = None

try:
    import sqlalchemy as sa
except ImportError:
    sa = None


class DataSourceService:
    """Manage database / API data-source connections."""

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[DataSource]:
        return db.query(DataSource).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, ds_id: int) -> Optional[DataSource]:
        return db.query(DataSource).filter(DataSource.id == ds_id).first()

    @staticmethod
    def create(db: Session, data: Dict[str, Any]) -> DataSource:
        ds = DataSource(**data)
        db.add(ds)
        db.commit()
        db.refresh(ds)
        return ds

    @staticmethod
    def update(db: Session, ds_id: int, data: Dict[str, Any]) -> Optional[DataSource]:
        ds = db.query(DataSource).filter(DataSource.id == ds_id).first()
        if not ds:
            return None
        for key, value in data.items():
            if hasattr(ds, key):
                setattr(ds, key, value)
        db.commit()
        db.refresh(ds)
        return ds

    @staticmethod
    def delete(db: Session, ds_id: int) -> bool:
        ds = db.query(DataSource).filter(DataSource.id == ds_id).first()
        if not ds:
            return False
        db.delete(ds)
        db.commit()
        return True

    # ------------------------------------------------------------------
    # Test connection
    # ------------------------------------------------------------------
    @staticmethod
    def test_connection(ds: DataSource) -> Dict[str, Any]:
        """Ping the remote data source and return connectivity info."""
        if ds.type == DataSourceType.mysql:
            return DataSourceService._test_mysql(ds)
        elif ds.type == DataSourceType.hive:
            return {"success": False, "message": "Hive connector not implemented"}
        elif ds.type == DataSourceType.csv:
            return {"success": True, "message": "CSV sources are local, no connection test required"}
        elif ds.type == DataSourceType.api:
            return {"success": False, "message": "API connector not implemented"}
        return {"success": False, "message": f"Unknown datasource type: {ds.type}"}

    @staticmethod
    def _test_mysql(ds: DataSource) -> Dict[str, Any]:
        if sa is None:
            return {"success": False, "message": "SQLAlchemy is not installed"}
        try:
            url = f"mysql+pymysql://{ds.user}:{ds.password_encrypted}@{ds.host}:{ds.port}/{ds.database_name}"
            engine = sa.create_engine(url, connect_args={"connect_timeout": 5})
            with engine.connect() as conn:
                conn.execute(sa.text("SELECT 1"))
            engine.dispose()
            return {"success": True, "message": "Connection successful"}
        except Exception as exc:
            return {"success": False, "message": str(exc)}

    # ------------------------------------------------------------------
    # Fetch table schemas
    # ------------------------------------------------------------------
    @staticmethod
    def get_tables(db: Session, ds_id: int) -> Dict[str, Any]:
        ds = DataSourceService.get_by_id(db, ds_id)
        if not ds:
            return {"success": False, "message": "Datasource not found"}
        try:
            url = f"mysql+pymysql://{ds.user}:{ds.password_encrypted}@{ds.host}:{ds.port}/{ds.database_name}"
            engine = sa.create_engine(url, connect_args={"connect_timeout": 5})
            inspector = sa.inspect(engine)
            tables = inspector.get_table_names()
            result = {}
            for table in tables:
                columns = [
                    {"name": col["name"], "type": str(col["type"])}
                    for col in inspector.get_columns(table)
                ]
                result[table] = columns
            engine.dispose()
            return {"success": True, "tables": result}
        except Exception as exc:
            return {"success": False, "message": str(exc)}

    # ------------------------------------------------------------------
    # Role binding
    # ------------------------------------------------------------------
    @staticmethod
    def bind_roles(db: Session, ds_id: int, roles: List[str]) -> Optional[DataSource]:
        ds = DataSourceService.get_by_id(db, ds_id)
        if not ds:
            return None
        ds.bind_roles = json.dumps(roles, ensure_ascii=False)
        db.commit()
        db.refresh(ds)
        return ds
