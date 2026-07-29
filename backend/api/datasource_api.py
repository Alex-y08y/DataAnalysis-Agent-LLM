from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.user import User
from models.datasource import DataSource, DataSourceType
from services.datasource_service import DataSourceService
from api.auth_api import get_current_user
from utils.db_utils import get_db

router = APIRouter(prefix="/api/datasources", tags=["datasources"])


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------
class DataSourceCreate(BaseModel):
    name: str
    type: DataSourceType
    host: str | None = None
    port: int | None = None
    user: str | None = None
    password_encrypted: str | None = None
    database_name: str | None = None
    extra_config: str | None = None
    bind_roles: str | None = None


class DataSourceUpdate(BaseModel):
    name: str | None = None
    host: str | None = None
    port: int | None = None
    user: str | None = None
    password_encrypted: str | None = None
    database_name: str | None = None
    extra_config: str | None = None
    bind_roles: str | None = None


class DataSourceOut(BaseModel):
    id: int
    name: str
    type: str
    host: str | None
    port: int | None
    database_name: str | None
    bind_roles: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestConnectionResult(BaseModel):
    success: bool
    message: str


class TableList(BaseModel):
    success: bool
    tables: dict[str, list[dict[str, str]]] | None = None
    message: str | None = None


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@router.get("", response_model=list[DataSourceOut])
def list_datasources(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return DataSourceService.get_all(db, skip, limit)


@router.get("/{ds_id}", response_model=DataSourceOut)
def get_datasource(ds_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    ds = DataSourceService.get_by_id(db, ds_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Datasource not found")
    return ds


@router.post("", response_model=DataSourceOut, status_code=201)
def create_datasource(
    body: DataSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = body.model_dump()
    data["created_by"] = current_user.id
    return DataSourceService.create(db, data)


@router.put("/{ds_id}", response_model=DataSourceOut)
def update_datasource(
    ds_id: int,
    body: DataSourceUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    ds = DataSourceService.update(db, ds_id, data)
    if not ds:
        raise HTTPException(status_code=404, detail="Datasource not found")
    return ds


@router.delete("/{ds_id}", status_code=204)
def delete_datasource(ds_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    ok = DataSourceService.delete(db, ds_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Datasource not found")


@router.post("/test", response_model=TestConnectionResult)
def test_connection(
    body: DataSourceCreate,
    _user: User = Depends(get_current_user),
):
    ds = DataSource(**body.model_dump())
    result = DataSourceService.test_connection(ds)
    return TestConnectionResult(**result)


@router.get("/{ds_id}/tables", response_model=TableList)
def get_tables(
    ds_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = DataSourceService.get_tables(db, ds_id)
    return TableList(**result)
