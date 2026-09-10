from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.core.deps import get_current_user
from app.db.models.user import User
from app.services.rag_pipeline import RAGPipeline
from pydantic import BaseModel
import uuid
from typing import Optional, List

router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

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
async def query_question(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Answer a question using RAG"""
    session_id = request.session_id or str(uuid.uuid4())
    
    # Use the RAG pipeline to answer the question
    pipeline = RAGPipeline()
    result = pipeline.answer_question(
        db=db,
        tenant_id=current_user.tenant_id,
        question=request.question
    )
    
    # Log the chat to database
    from app.db.models.chat_log import ChatLog
    chat_log = ChatLog(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        question=request.question,
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