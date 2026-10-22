"""Document-level access control. Every place that lists, searches or changes documents goes through here."""
from sqlalchemy import or_, select
from app.db.models.document import Document, DocumentAccess, VISIBILITY_EVERYONE
from app.db.models.user import User


def visible_document_ids(user: User):
    """A SELECT of the ids of the documents `user` may see; pass it to `.in_()` to filter documents or chunks"""
    query = select(Document.id).where(Document.tenant_id == user.tenant_id)
    if user.is_admin:
        return query
    granted = select(DocumentAccess.document_id).where(DocumentAccess.user_id == user.id)
    return query.where(or_(
        Document.visibility == VISIBILITY_EVERYONE,
        Document.owner_id == user.id,
        Document.id.in_(granted),
    ))


def can_manage(user: User, document: Document) -> bool:
    """Whether `user` may change who can see `document`, or delete it"""
    return document.tenant_id == user.tenant_id and (user.is_admin or document.owner_id == user.id)
