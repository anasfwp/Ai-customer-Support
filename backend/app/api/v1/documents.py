from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.core.deps import get_current_user
from app.core.permissions import can_manage, visible_document_ids
from app.db.models.user import User
from app.db.models.document import Document, DocumentAccess, DocumentStatus, VISIBILITY_RESTRICTED
from app.db.models.chunk import Chunk
from app.services.document_parser import DocumentParser
from app.services.chunker import Chunker
from app.services.embedding_service import EmbeddingService
from app.config import settings
from pydantic import BaseModel
from typing import List, Literal
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a document for processing"""
    # Validate file type
    allowed_extensions = ['.pdf', '.docx', '.txt']
    if not file.filename or '.' not in file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a name with an extension"
        )
    file_ext = '.' + file.filename.split('.')[-1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not supported. Allowed: {allowed_extensions}"
        )

    # Read file content, enforcing a size cap so a huge upload can't
    # exhaust server memory (this loads the whole file into RAM below).
    content = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB upload limit"
        )
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty"
        )

    # Create document record
    doc_id = str(uuid.uuid4())
    document = Document(
        id=doc_id,
        tenant_id=current_user.tenant_id,
        owner_id=current_user.id,
        filename=file.filename,
        status=DocumentStatus.PROCESSING
    )
    db.add(document)
    db.commit()

    try:
        parser = DocumentParser()
        chunker = Chunker()
        
        # Parse based on file type
        if file_ext == '.pdf':
            pages = parser.parse_pdf(content)
        elif file_ext == '.docx':
            pages = parser.parse_docx(content)
        else:  # .txt
            pages = parser.parse_txt(content)
        
        if not pages:
            raise ValueError("No text extracted from document")
        
        # Chunk the document
        chunks = chunker.chunk_pages(pages)
        
        # Add metadata to each chunk
        for chunk in chunks:
            chunk['metadata']['document_id'] = doc_id
            chunk['metadata']['filename'] = file.filename
            chunk['metadata']['tenant_id'] = current_user.tenant_id
        
        # Generate embeddings
        embedding_service = EmbeddingService()
        texts = [chunk['content'] for chunk in chunks]
        
        try:
            embeddings = embedding_service.embed_texts(texts)
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}. Storing chunks without embeddings.")
            embeddings = [None] * len(chunks)
        
        # Store chunks in database
        for chunk, embedding in zip(chunks, embeddings):
            db_chunk = Chunk(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                tenant_id=current_user.tenant_id,
                content=chunk['content'],
                embedding=embedding,
                chunk_metadata=chunk['metadata']
            )
            db.add(db_chunk)
        
        # Update document status
        document.status = DocumentStatus.READY
        document.chunk_count = len(chunks)
        db.commit()
        
        return {
            "document_id": doc_id,
            "status": "ready",
            "chunk_count": len(chunks)
        }
        
    except Exception as e:
        logger.error(f"Document processing error for document {doc_id}: {e}", exc_info=True)
        document.status = DocumentStatus.FAILED
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document. Please check the file and try again."
        )

@router.get("/")
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List the documents the current user may see"""
    documents = db.query(Document).filter(
        Document.id.in_(visible_document_ids(current_user))
    ).order_by(Document.created_at.desc()).all()
    emails = dict(db.query(User.id, User.email).filter(User.tenant_id == current_user.tenant_id).all())
    shared = {}
    for document_id, user_id in db.query(DocumentAccess.document_id, DocumentAccess.user_id).filter(
        DocumentAccess.document_id.in_([doc.id for doc in documents])
    ):
        shared.setdefault(document_id, []).append(user_id)

    return [_document_out(doc, current_user, emails, shared.get(doc.id, [])) for doc in documents]


def _document_out(doc: Document, user: User, emails: dict, shared_with: List[str]) -> dict:
    manageable = can_manage(user, doc)
    return {
        "id": doc.id,
        "filename": doc.filename,
        "status": doc.status.value,
        "chunk_count": doc.chunk_count,
        "created_at": doc.created_at,
        "visibility": doc.visibility,
        "owner_email": emails.get(doc.owner_id),
        "can_manage": manageable,
        # who it is shared with is only shown to people who can change it
        "shared_with": shared_with if manageable else [],
    }


class AccessUpdate(BaseModel):
    visibility: Literal["everyone", "restricted"]
    user_ids: List[str] = []


@router.put("/{document_id}/access")
async def update_document_access(
    document_id: str,
    access: AccessUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set who can see a document: everyone in the company, or only the listed users (plus its owner and admins)"""
    document = _manageable_document(db, document_id, current_user)

    user_ids = set(access.user_ids) if access.visibility == VISIBILITY_RESTRICTED else set()
    if user_ids:
        found = {uid for (uid,) in db.query(User.id).filter(User.id.in_(user_ids), User.tenant_id == current_user.tenant_id)}
        if found != user_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Some users are not in your company")

    document.visibility = access.visibility
    db.query(DocumentAccess).filter(DocumentAccess.document_id == document_id).delete()
    db.add_all(DocumentAccess(document_id=document_id, user_id=uid) for uid in user_ids)
    db.commit()

    emails = dict(db.query(User.id, User.email).filter(User.tenant_id == current_user.tenant_id).all())
    return _document_out(document, current_user, emails, sorted(user_ids))


def _manageable_document(db: Session, document_id: str, user: User) -> Document:
    """The document if `user` may manage it; 404 if they can't see it at all, 403 if they can see but not manage it"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.id.in_(visible_document_ids(user))
    ).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if not can_manage(user, document):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the document's owner or an admin can do that")
    return document

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document and all its chunks (owner or admin only)"""
    document = _manageable_document(db, document_id, current_user)

    # Delete all chunks and access grants
    db.query(Chunk).filter(Chunk.document_id == document_id).delete()
    db.query(DocumentAccess).filter(DocumentAccess.document_id == document_id).delete()
    
    # Delete document
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}