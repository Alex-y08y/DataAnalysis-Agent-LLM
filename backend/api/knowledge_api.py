from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.user import User
from models.knowledge_document import KnowledgeDocument, DocType, DocStatus
from api.auth_api import get_current_user
from utils.db_utils import get_db

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------
class DocumentOut(BaseModel):
    id: int
    title: str
    doc_type: str
    file_path: str | None
    content_summary: str | None
    chunk_count: int
    metadata_tags: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentUpdate(BaseModel):
    title: str | None = None
    content_summary: str | None = None
    metadata_tags: str | None = None
    status: str | None = None


# --------------------------------------------------------------------------
# Routes  — CRUD
# --------------------------------------------------------------------------
@router.get("/documents", response_model=list[DocumentOut])
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return db.query(KnowledgeDocument).offset(skip).limit(limit).all()


@router.get("/documents/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.put("/documents/{doc_id}", response_model=DocumentOut)
def update_document(
    doc_id: int,
    body: DocumentUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(doc, k, v)
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/documents/{doc_id}", status_code=204)
def delete_document(doc_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()


# --------------------------------------------------------------------------
# Upload
# --------------------------------------------------------------------------
@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Detect type from filename
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "txt"
    type_map = {"pdf": DocType.pdf, "txt": DocType.txt, "md": DocType.md, "xlsx": DocType.excel, "xls": DocType.excel}
    doc_type = type_map.get(ext, DocType.txt)

    doc = KnowledgeDocument(
        title=title or (file.filename or "untitled"),
        doc_type=doc_type,
        file_path=f"/uploads/{file.filename}" if file.filename else None,
        status=DocStatus.ready,
        created_by=current_user.id,
        chunk_count=0,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    # TODO: actually persist the file and run chunking/embedding
    return doc


# --------------------------------------------------------------------------
# Rebuild index
# --------------------------------------------------------------------------
@router.post("/rebuild")
def rebuild_index(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    # TODO: re-embed all documents
    return {"message": "Index rebuild triggered", "status": "ok"}
