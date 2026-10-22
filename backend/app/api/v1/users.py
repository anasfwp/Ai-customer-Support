from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.core.deps import get_current_user, get_db, require_admin
from app.core.limiter import limiter
from app.core.security import get_password_hash
from app.db.models.user import User
from app.api.v1.auth import MIN_PASSWORD_LENGTH

router = APIRouter()


class MemberCreate(BaseModel):
    email: EmailStr
    password: str
    is_admin: bool = False


def _member_out(user: User) -> dict:
    return {"id": user.id, "email": user.email, "is_admin": user.is_admin, "created_at": user.created_at}


@router.get("/")
async def list_members(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Everyone in the current user's company (used to pick who a document is shared with)"""
    members = db.query(User).filter(User.tenant_id == current_user.tenant_id).order_by(User.created_at).all()
    return [_member_out(user) for user in members]


@router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def add_member(request: Request, member: MemberCreate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Create an account inside the admin's company; the admin passes the password on to the new member"""
    if len(member.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")
    if db.query(User).filter(User.email == member.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=member.email,
        hashed_password=get_password_hash(member.password),
        tenant_id=current_user.tenant_id,
        is_admin=member.is_admin
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _member_out(user)
