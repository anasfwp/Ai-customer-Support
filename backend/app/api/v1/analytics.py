from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.base import SessionLocal
from app.core.deps import require_admin
from app.db.models.user import User
from app.db.models.chat_log import ChatLog
from app.db.models.document import Document
from datetime import datetime, timedelta

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/usage")
async def get_usage_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get usage statistics"""
    
    # Total queries
    total_queries = db.query(ChatLog).filter(
        ChatLog.tenant_id == current_user.tenant_id
    ).count()
    
    # Fallback rate (questions AI couldn't answer)
    fallback_count = db.query(ChatLog).filter(
        ChatLog.tenant_id == current_user.tenant_id,
        ChatLog.fallback == True
    ).count()
    
    fallback_rate = (fallback_count / total_queries * 100) if total_queries > 0 else 0
    
    # Total documents
    total_documents = db.query(Document).filter(
        Document.tenant_id == current_user.tenant_id
    ).count()
    
    # Top questions
    top_questions = db.query(
        ChatLog.question,
        func.count(ChatLog.question).label('count')
    ).filter(
        ChatLog.tenant_id == current_user.tenant_id
    ).group_by(ChatLog.question).order_by(func.count(ChatLog.question).desc()).limit(10).all()
    
    return {
        "total_queries": total_queries,
        "fallback_rate": fallback_rate,
        "total_documents": total_documents,
        "top_questions": [{"question": q[0], "count": q[1]} for q in top_questions]
    }

@router.get("/unanswered")
async def get_unanswered_questions(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get questions that couldn't be answered (content gaps)"""
    
    unanswered = db.query(ChatLog).filter(
        ChatLog.tenant_id == current_user.tenant_id,
        ChatLog.fallback == True
    ).order_by(ChatLog.created_at.desc()).limit(20).all()
    
    return [
        {
            "question": log.question,
            "created_at": log.created_at
        }
        for log in unanswered
    ]