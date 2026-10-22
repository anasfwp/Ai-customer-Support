from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.db.models.user import User
from app.services.rag_pipeline import RAGPipeline
from pydantic import BaseModel, field_validator
import json
import logging
import uuid
from typing import Optional, List

router = APIRouter()
logger = logging.getLogger(__name__)

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
    chat_log_id: Optional[str] = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _save_chat_log(db: Session, tenant_id: str, user_id: str, question: str, result: dict, session_id: str) -> str:
    from app.db.models.chat_log import ChatLog
    chat_log = ChatLog(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        user_id=user_id,
        question=question,
        answer=result["answer"],
        citations=result.get("citations", []),
        confidence=str(result.get("confidence", 0.0)),
        fallback=result.get("fallback", True),
        session_id=session_id
    )
    db.add(chat_log)
    db.commit()
    return chat_log.id

def _pipeline() -> RAGPipeline:
    try:
        return RAGPipeline()
    except ValueError as e:
        # Provider not configured (e.g. missing/placeholder API key)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

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

    result = _pipeline().answer_question(
        db=db,
        tenant_id=current_user.tenant_id,
        question=chat_request.question
    )
    chat_log_id = _save_chat_log(db, current_user.tenant_id, current_user.id, chat_request.question, result, session_id)
    
    return ChatResponse(
        answer=result["answer"],
        citations=result.get("citations", []),
        confidence=result.get("confidence", 0.0),
        fallback=result.get("fallback", True),
        session_id=session_id,
        chat_log_id=chat_log_id
    )

def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"

@router.post("/stream")
@limiter.limit("20/minute")
async def stream_question(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Answer a question using RAG, streamed as server-sent events: meta, token..., then done (or error)"""
    session_id = chat_request.session_id or str(uuid.uuid4())
    question = chat_request.question
    tenant_id, user_id = current_user.tenant_id, current_user.id
    pipeline = _pipeline()
    try:
        result = pipeline.retrieve(db, tenant_id, question)
    except Exception:
        logger.exception("RAG retrieval error for tenant %s", tenant_id)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="I encountered an error processing your question. Please try again.")
    context = result.pop("context", None)

    def events():
        yield _sse("meta", {"citations": result["citations"], "confidence": result["confidence"], "fallback": result["fallback"], "session_id": session_id})
        try:
            if context is None:
                yield _sse("token", {"text": result["answer"]})
            else:
                parts = []
                for token in pipeline.llm_provider.stream_answer(question, context):
                    parts.append(token)
                    yield _sse("token", {"text": token})
                result["answer"] = "".join(parts)
            # The request's session is closed once streaming starts, so log with a fresh one
            log_db = SessionLocal()
            try:
                chat_log_id = _save_chat_log(log_db, tenant_id, user_id, question, result, session_id)
            finally:
                log_db.close()
        except Exception:
            logger.exception("RAG streaming error for tenant %s", tenant_id)
            yield _sse("error", {"detail": "I encountered an error generating the answer. Please try again."})
            return
        yield _sse("done", {"chat_log_id": chat_log_id})

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

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