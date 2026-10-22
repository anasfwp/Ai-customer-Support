from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.models import tenant, user, document, chunk, chat_log, feedback  # noqa: F401  registers tables for FKs
from app.db.models.chunk import Chunk
from app.services.retriever import Retriever, bm25, reciprocal_rank_fusion


class FakeEmbeddings:
    def embed_texts(self, texts):
        return [_vec(1, 0)]


def _vec(x, y):
    return [x, y] + [0.0] * 1534


def _db(*chunks):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    db.add_all(chunks)
    db.commit()
    return db


def test_retrieve_ranks_by_cosine_and_isolates_tenants():
    db = _db(
        Chunk(id="near", document_id="d", tenant_id="t1", content="a", embedding=_vec(1, 0.1)),
        Chunk(id="far", document_id="d", tenant_id="t1", content="b", embedding=_vec(0, 1)),
        Chunk(id="other", document_id="d", tenant_id="t2", content="c", embedding=_vec(1, 0)),
    )

    results = Retriever(FakeEmbeddings(), rerank=False).retrieve(db, "t1", "q", top_k=5)

    assert [c.id for c, _ in results] == ["near", "far"]
    assert results[0][1] > 0.99 and abs(results[1][1]) < 1e-9


def test_keyword_search_rescues_exact_term_that_vectors_miss():
    db = _db(*[
        Chunk(id=f"n{i}", document_id="d", tenant_id="t", content=f"general billing text {i}", embedding=_vec(1, 0.1 * i))
        for i in range(1, 6)
    ], Chunk(id="code", document_id="d", tenant_id="t", content="ERR-4012 means the token expired", embedding=_vec(0, 1)))

    vector_only = Retriever(FakeEmbeddings(), hybrid=False, rerank=False).retrieve(db, "t", "what is ERR-4012", top_k=2)
    hybrid = Retriever(FakeEmbeddings(), rerank=False).retrieve(db, "t", "what is ERR-4012", top_k=2)

    assert "code" not in [c.id for c, _ in vector_only]
    assert "code" in [c.id for c, _ in hybrid]


def test_rrf_rewards_agreement():
    a, b, c = (Chunk(id=i) for i in "abc")
    fused = reciprocal_rank_fusion([[(a, 0), (b, 0)], [(b, 0), (c, 0)]])
    assert [x.id for x, _ in fused] == ["b", "a", "c"]


def test_bm25_prefers_rare_matching_term():
    scores = bm25("refund window", ["the refund window is 30 days", "the shipping window", "unrelated"])
    assert scores[0] > scores[1] > scores[2] == 0
