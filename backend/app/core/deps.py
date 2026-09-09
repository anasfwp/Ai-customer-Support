from fastapi import Depends, HTTPException, status 
from fastapi.security import OAuth2PasswordBearer 
from sqlalchemy.orm import Session 
from app.db.base import SessionLocal 
from app.db.models.user import User 
from app.core.security import decode_token 
 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login") 
 
def get_db(): 
    db = SessionLocal() 
    try: 
        yield db 
    finally: 
        db.close() 
 
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)): 
    payload = decode_token(token) 
    if not payload: 
        raise HTTPException( 
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid authentication credentials" 
        ) 
 
    email = payload.get("sub") 
    tenant_id = payload.get("tenant_id") 
 
    if not email or not tenant_id: 
        raise HTTPException( 
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token payload" 
        ) 
 
    user = db.query(User).filter(User.email == email, User.tenant_id == tenant_id).first() 
    if not user: 
        raise HTTPException( 
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="User not found" 
        ) 
 
    return user 
