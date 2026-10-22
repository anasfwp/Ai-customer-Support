from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.permissions import can_manage, visible_document_ids
from app.db.base import Base
from app.db.models import tenant, user, document, chunk, chat_log, feedback  # noqa: F401  registers tables for FKs
from app.db.models.chunk import Chunk
from app.db.models.document import Document, DocumentAccess
from app.db.models.tenant import Tenant
from app.db.models.user import User
from app.services.retriever import Retriever


class FakeEmbeddings:
    def embed_texts(self, texts):
        return [[1.0] + [0.0] * 1535]


def _db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    db.add_all([Tenant(id="t1", name="Acme"), Tenant(id="t2", name="Other")])
    db.add_all([
        User(id="admin", email="admin@acme.com", hashed_password="x", tenant_id="t1", is_admin=True),
        User(id="alice", email="alice@acme.com", hashed_password="x", tenant_id="t1", is_admin=False),
        User(id="bob", email="bob@acme.com", hashed_password="x", tenant_id="t1", is_admin=False),
        User(id="eve", email="eve@other.com", hashed_password="x", tenant_id="t2", is_admin=True),
    ])
    db.add_all([
        Document(id="public", tenant_id="t1", owner_id="admin", filename="faq.txt"),
        Document(id="legacy", tenant_id="t1", owner_id=None, filename="old.txt"),  # uploaded before owners existed
        Document(id="alice_private", tenant_id="t1", owner_id="alice", visibility="restricted", filename="salaries.txt"),
        Document(id="shared_with_bob", tenant_id="t1", owner_id="alice", visibility="restricted", filename="plan.txt"),
        Document(id="other_tenant", tenant_id="t2", owner_id="eve", filename="theirs.txt"),
    ])
    db.add(DocumentAccess(document_id="shared_with_bob", user_id="bob"))
    db.add_all(Chunk(id=f"c_{d}", document_id=d, tenant_id=t, content=d, embedding=[1.0] + [0.0] * 1535)
               for d, t in [("public", "t1"), ("legacy", "t1"), ("alice_private", "t1"), ("shared_with_bob", "t1"), ("other_tenant", "t2")])
    db.commit()
    return db


def _visible(db, user_id):
    return {doc_id for (doc_id,) in db.execute(visible_document_ids(db.get(User, user_id)))}


def test_admin_sees_every_document_in_their_company_only():
    db = _db()
    assert _visible(db, "admin") == {"public", "legacy", "alice_private", "shared_with_bob"}
    assert _visible(db, "eve") == {"other_tenant"}


def test_members_see_public_own_and_shared_documents():
    db = _db()
    assert _visible(db, "alice") == {"public", "legacy", "alice_private", "shared_with_bob"}
    assert _visible(db, "bob") == {"public", "legacy", "shared_with_bob"}


def test_retrieval_never_returns_chunks_of_hidden_documents():
    db = _db()
    bob = db.get(User, "bob")
    results = Retriever(FakeEmbeddings(), hybrid=False, rerank=False).retrieve(db, "t1", "q", top_k=10, document_ids=visible_document_ids(bob))
    assert {c.document_id for c, _ in results} == {"public", "legacy", "shared_with_bob"}


def test_only_owner_or_admin_can_manage():
    db = _db()
    doc = db.get(Document, "shared_with_bob")
    assert can_manage(db.get(User, "alice"), doc)
    assert can_manage(db.get(User, "admin"), doc)
    assert not can_manage(db.get(User, "bob"), doc)
    assert not can_manage(db.get(User, "eve"), doc)  # admin of another company
