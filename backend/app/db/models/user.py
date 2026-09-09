from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey 
from sqlalchemy.sql import func 
from app.db.base import Base 
import uuid 
 
class User(Base): 
    __tablename__ = "users" 
 
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())) 
    email = Column(String, unique=True, index=True, nullable=False) 
    hashed_password = Column(String, nullable=False) 
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False) 
    is_admin = Column(Boolean, default=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 
