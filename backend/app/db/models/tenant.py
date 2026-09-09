from sqlalchemy import Column, String, DateTime, JSON 
from sqlalchemy.sql import func 
from app.db.base import Base 
import uuid 
 
class Tenant(Base): 
    __tablename__ = "tenants" 
 
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())) 
    name = Column(String, nullable=False) 
    branding = Column(JSON, default={}) 
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 
