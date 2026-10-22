from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum
from sqlalchemy.sql import func
from app.db.base import Base
import uuid
import enum

class DocumentStatus(enum.Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

# Who can see a document (and retrieve its chunks). Its owner and tenant admins always can.
VISIBILITY_EVERYONE = "everyone"      # every user in the tenant
VISIBILITY_RESTRICTED = "restricted"  # only users listed in document_access

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=True)  # null for documents uploaded before ownership existed
    visibility = Column(String, nullable=False, default=VISIBILITY_EVERYONE, server_default=VISIBILITY_EVERYONE)
    filename = Column(String, nullable=False)
    file_url = Column(String, nullable=True)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PROCESSING)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DocumentAccess(Base):
    """A user granted access to a restricted document"""
    __tablename__ = "document_access"

    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
