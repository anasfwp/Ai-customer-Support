from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.core.deps import get_current_user
from app.db.models.user import User
from app.db.models.feedback import Feedback
from app.db.models.chat_log import ChatLog
from pydantic import BaseModel
import uuid

router = APIRouter()

class FeedbackRequest(BaseModel):
    chat_log_id: str
    helpful: bool
    comment: str = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
async def submit_feedback(
    feedback_data: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit feedback for a chat response"""
    
    # Verify the chat log exists and belongs to this tenant
    chat_log = db.query(ChatLog).filter(
        ChatLog.id == feedback_data.chat_log_id,
        ChatLog.tenant_id == current_user.tenant_id
    ).first()
    
    if not chat_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat log not found"
        )
    
    # Create feedback
    feedback = Feedback(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        chat_log_id=feedback_data.chat_log_id,
        helpful=feedback_data.helpful,
        comment=feedback_data.comment
    )
    
    db.add(feedback)
    db.commit()
    
    return {"message": "Feedback submitted successfully", "feedback_id": feedback.id}

@router.get("/stats")
async def get_feedback_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get feedback statistics"""
    total = db.query(Feedback).filter(
        Feedback.tenant_id == current_user.tenant_id
    ).count()
    
    helpful = db.query(Feedback).filter(
        Feedback.tenant_id == current_user.tenant_id,
        Feedback.helpful == True
    ).count()
    
    unhelpful = total - helpful
    
    return {
        "total_feedback": total,
        "helpful": helpful,
        "unhelpful": unhelpful,
        "satisfaction_rate": (helpful / total * 100) if total > 0 else 0
    }