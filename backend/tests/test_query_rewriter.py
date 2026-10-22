from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.models import tenant, user, document, chunk, chat_log, feedback  # noqa: F401  registers tables for FKs
from app.db.models.chunk import Chunk
from app.services.query_rewriter import rewrite_query
from app.services.retriever import Retriever

HISTORY = [{"question": "Do you ship internationally?", "answer": "Yes, to over 50 countries."}]


class FakeLLM:
    def __init__(self, reply=None, error=None):
        self.reply, self.error, self.prompts = reply, error, []

    def stream(self, prompt, system="", timeout=None):
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        yield self.reply


def test_rewrite_uses_the_conversation_and_returns_the_query():
    llm = FakeLLM("How long does international shipping take?")
    assert rewrite_query(llm, "How long does it take?", HISTORY) == "How long does international shipping take?"
    assert "Do you ship internationally?" in llm.prompts[0]


def test_rewrite_keeps_only_the_question_line():
    llm = FakeLLM('STANDALONE QUESTION: "How long does international shipping take?"\n\nThis resolves "it" to shipping.')
    assert rewrite_query(llm, "How long does it take?", HISTORY) == "How long does international shipping take?"


def test_rewrite_falls_back_to_previous_question_plus_follow_up():
    expected = "Do you ship internationally? How long does it take?"
    assert rewrite_query(FakeLLM(error=TimeoutError("deadline exceeded")), "How long does it take?", HISTORY) == expected
    assert rewrite_query(FakeLLM("   "), "How long does it take?", HISTORY) == expected
    assert rewrite_query(FakeLLM("x" * 1000), "How long does it take?", HISTORY) == expected
    assert rewrite_query(FakeLLM(error=TimeoutError()), "Do you ship to Canada?", []) == "Do you ship to Canada?"


class PerQueryEmbeddings:
    """'shipping' queries point at one chunk, everything else at the other"""
    def embed_texts(self, texts):
        return [[1.0, 0.0] + [0.0] * 1534 if "shipping" in t else [0.0, 1.0] + [0.0] * 1534 for t in texts]


def test_extra_queries_are_searched_and_fused():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    db.add_all([
        Chunk(id="shipping", document_id="d", tenant_id="t", content="a", embedding=[1.0, 0.0] + [0.0] * 1534),
        Chunk(id="other", document_id="d", tenant_id="t", content="b", embedding=[0.0, 1.0] + [0.0] * 1534),
    ])
    db.commit()
    retriever = Retriever(PerQueryEmbeddings(), hybrid=False, rerank=False)

    results = retriever.retrieve(db, "t", "international shipping time", top_k=2, extra_queries=["how long?"])

    # each chunk keeps its best similarity across the two queries
    assert {c.id: round(sim, 3) for c, sim in results} == {"shipping": 1.0, "other": 1.0}
