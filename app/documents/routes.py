from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.models import Document, DocumentStatus, User
from app.db.session import get_db
from app.documents.schemas import DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Phase 1: registers the document and stores it as 'pending'.
    Phase 4 wires this to a Celery task that does the actual
    extract -> chunk -> embed -> index work in the background,
    then flips status to 'ready' (or 'failed' with error_message set).
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    document = Document(
        org_id=current_user.org_id,
        uploaded_by=current_user.id,
        filename=file.filename,
        status=DocumentStatus.pending,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # TODO (Phase 4): enqueue_ingestion_task.delay(document.id, contents)

    return document


@router.get("", response_model=list[DocumentOut])
def list_documents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Document)
        .filter(Document.org_id == current_user.org_id)
        .order_by(Document.created_at.desc())
        .all()
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.org_id == current_user.org_id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    db.delete(document)
    db.commit()
    # TODO (Phase 2+): also delete this document's vectors from Qdrant, filtered by org_id + document_id
