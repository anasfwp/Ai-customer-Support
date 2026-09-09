from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum 
from sqlalchemy.sql import func 
from app.db.base import Base 
import uuid 
import enum 
 
class DocumentStatus(enum.Enum): 
    PROCESSING = "processing" 
    READY = "ready" 
    FAILED = "failed" 
 
class Document(Base): 
    __tablename__ = "documents" 
 
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())) 
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False) 
    filename = Column(String, nullable=False) 
    file_url = Column(String, nullable=True) 
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PROCESSING) 
    chunk_count = Column(Integer, default=0) 
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 
