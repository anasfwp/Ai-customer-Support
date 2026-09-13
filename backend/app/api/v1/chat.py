from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.db.models.user import User
from app.services.rag_pipeline import RAGPipeline
from pydantic import BaseModel, field_validator
import uuid
from typing import Optional, List

router = APIRouter()

MAX_QUESTION_LENGTH = 2000

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

    @field_validator("question")
    @classmethod
    def question_not_blank(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty")
        if len(v) > MAX_QUESTION_LENGTH:
            raise ValueError(f"Question must be at most {MAX_QUESTION_LENGTH} characters")
        return v

class ChatResponse(BaseModel):
    answer: str
    citations: List[dict] = []
    confidence: float = 0.0
    fallback: bool = False
    session_id: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/query", response_model=ChatResponse)
@limiter.limit("20/minute")
async def query_question(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Answer a question using RAG"""
    session_id = chat_request.session_id or str(uuid.uuid4())

    # Use the RAG pipeline to answer the question
    try:
        pipeline = RAGPipeline()
    except ValueError as e:
        # Provider not configured (e.g. missing/placeholder API key)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    result = pipeline.answer_question(
        db=db,
        tenant_id=current_user.tenant_id,
        question=chat_request.question
    )
    
    # Log the chat to database
    from app.db.models.chat_log import ChatLog
    chat_log = ChatLog(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        question=chat_request.question,
        answer=result["answer"],
        citations=result.get("citations", []),
        confidence=str(result.get("confidence", 0.0)),
        fallback=result.get("fallback", True),
        session_id=session_id
    )
    db.add(chat_log)
    db.commit()
    
    return ChatResponse(
        answer=result["answer"],
        citations=result.get("citations", []),
        confidence=result.get("confidence", 0.0),
        fallback=result.get("fallback", True),
        session_id=session_id
    )

@router.get("/history")
async def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get chat history for the current user"""
    from app.db.models.chat_log import ChatLog
    
    logs = db.query(ChatLog).filter(
        ChatLog.tenant_id == current_user.tenant_id
    ).order_by(ChatLog.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": log.id,
            "question": log.question,
            "answer": log.answer,
            "citations": log.citations,
            "confidence": log.confidence,
            "fallback": log.fallback,
            "session_id": log.session_id,
            "created_at": log.created_at
        }
        for log in logs
    ]