from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.core.deps import get_current_user
from app.db.models.user import User
from app.db.models.document import Document, DocumentStatus
from app.db.models.chunk import Chunk
from app.services.document_parser import DocumentParser
from app.services.chunker import Chunker
from app.services.embedding_service import EmbeddingService
from app.config import settings
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
    """List all documents for the current tenant"""
    documents = db.query(Document).filter(
        Document.tenant_id == current_user.tenant_id
    ).all()
    
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "status": doc.status.value,
            "chunk_count": doc.chunk_count,
            "created_at": doc.created_at
        }
        for doc in documents
    ]

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document and all its chunks"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.tenant_id == current_user.tenant_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete all chunks
    db.query(Chunk).filter(Chunk.document_id == document_id).delete()
    
    # Delete document
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}