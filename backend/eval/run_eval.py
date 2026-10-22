"""Evaluate retrieval recall and answer faithfulness on eval/dataset.jsonl, and follow-up query rewriting on eval/followups.jsonl.

Usage (from backend/):  python -m eval.run_eval --db-url postgresql://postgres:postgres@localhost:5433/support

Ingests eval/corpus/*.txt under a throwaway tenant, scores three retrieval setups, generates answers with the
production pipeline, has the LLM judge faithfulness, writes eval/results.md, then deletes the tenant's data.
"""
import argparse
import json
import re
import uuid
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import tenant, user, document, chunk, chat_log, feedback  # noqa: F401  registers tables
from app.db.models.chunk import Chunk
from app.db.models.document import Document, DocumentStatus
from app.db.models.tenant import Tenant
from app.services.chunker import Chunker
from app.services.document_parser import DocumentParser
from app.services.embedding_service import EmbeddingService
from app.services.rag_pipeline import RAGPipeline
from app.services.query_rewriter import fallback_query, rewrite_query
from app.services.retriever import Retriever

HERE = Path(__file__).parent
CONFIGS = [("vector only", False, False), ("hybrid (vector + keyword, RRF)", True, False), ("hybrid + rerank", True, True)]

JUDGE_PROMPT = """You are checking whether an answer is faithful to its context.
List each factual claim in the ANSWER, and mark it SUPPORTED if the CONTEXT states it, otherwise UNSUPPORTED.
Statements like "I don't know" are not claims. End with one line exactly in the form: SCORE: <supported>/<total>

CONTEXT:
{context}

ANSWER:
{answer}"""


def norm(s: str) -> str:
    return " ".join(s.lower().split())


class CachedEmbeddings:
    """Embed each question once across all configs"""
    def __init__(self, inner):
        self.inner, self.cache = inner, {}

    def embed_texts(self, texts):
        missing = [t for t in texts if t not in self.cache]
        if missing:
            self.cache.update(zip(missing, self.inner.embed_texts(missing)))
        return [self.cache[t] for t in texts]


def ingest(db, tenant_id: str, embeddings) -> int:
    """Same parse -> chunk -> embed steps as the upload endpoint"""
    count = 0
    for path in sorted((HERE / "corpus").glob("*.txt")):
        doc = Document(id=str(uuid.uuid4()), tenant_id=tenant_id, filename=path.name, status=DocumentStatus.READY)
        db.add(doc)
        db.flush()  # models have no relationships, so the document row must exist before its chunks reference it
        chunks = Chunker().chunk_pages(DocumentParser.parse_txt(path.read_bytes()))
        for c, emb in zip(chunks, embeddings.embed_texts([c["content"] for c in chunks])):
            c["metadata"].update(document_id=doc.id, filename=path.name, tenant_id=tenant_id)
            db.add(Chunk(id=str(uuid.uuid4()), document_id=doc.id, tenant_id=tenant_id, content=c["content"],
                         embedding=emb, chunk_metadata=c["metadata"]))
        doc.chunk_count = len(chunks)
        count += len(chunks)
    db.commit()
    return count


def first_hit_rank(results, evidence: str):
    for rank, (c, _) in enumerate(results, 1):
        if norm(evidence) in norm(c.content):
            return rank
    return None


def judge(llm, context, answer) -> float:
    verdict = "".join(llm.stream(JUDGE_PROMPT.format(context="\n---\n".join(context), answer=answer),
                                 system="You are a strict, careful evaluator."))
    m = re.search(r"SCORE:\s*(\d+)\s*/\s*(\d+)", verdict)
    if not m:
        raise ValueError(f"Judge returned no score: {verdict[-200:]}")
    supported, total = int(m.group(1)), int(m.group(2))
    return 1.0 if total == 0 else supported / total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-url", required=True, help="a dev/eval database; a throwaway tenant is created and removed")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--skip-generation", action="store_true", help="skip answer generation and the faithfulness judge (LLM calls)")
    parser.add_argument("--skip-followups", action="store_true", help="skip the follow-up query rewriting eval (LLM calls)")
    args = parser.parse_args()

    engine = create_engine(args.db_url)
    if engine.dialect.name == "postgresql":
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    dataset = [json.loads(line) for line in (HERE / "dataset.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    embeddings = CachedEmbeddings(EmbeddingService())

    tenant_row = Tenant(id=str(uuid.uuid4()), name="eval")
    db.add(tenant_row)
    db.commit()
    try:
        n_chunks = ingest(db, tenant_row.id, embeddings)
        print(f"Ingested {n_chunks} chunks; {len(dataset)} questions; backend={engine.dialect.name}")

        rows = []
        for name, hybrid, rerank in CONFIGS:
            retriever = Retriever(embeddings, hybrid=hybrid, rerank=rerank)
            ranks = [first_hit_rank(retriever.retrieve(db, tenant_row.id, q["question"], top_k=args.k), q["evidence"]) for q in dataset]
            recall = lambda k: sum(1 for r in ranks if r and r <= k) / len(ranks)
            mrr = sum(1 / r for r in ranks if r) / len(ranks)
            rows.append((name, recall(1), recall(3), recall(args.k), mrr))
            misses = [q["question"] for q, r in zip(dataset, ranks) if not r]
            print(f"{name}: recall@{args.k}={recall(args.k):.3f} mrr={mrr:.3f} misses={misses}")

        followup_rows = None
        if not args.skip_followups:
            followup_rows = eval_followups(db, tenant_row.id, embeddings, args.k)

        faithfulness = answered = None
        if not args.skip_generation:
            pipeline = RAGPipeline()
            pipeline.retriever.embedding_service = embeddings
            scores, n_answered = [], 0
            for q in dataset:
                result = pipeline.retrieve(db, tenant_row.id, q["question"])
                if "context" not in result:
                    continue
                answer = pipeline.llm_provider.generate_answer(q["question"], result["context"])
                n_answered += "know" not in answer.lower()
                scores.append(judge(pipeline.llm_provider, result["context"], answer))
            faithfulness = sum(scores) / len(scores)
            answered = n_answered / len(dataset)
            print(f"faithfulness={faithfulness:.3f} answered={answered:.3f}")

        write_report(rows, faithfulness, answered, args.k, len(dataset), n_chunks, engine.dialect.name, followup_rows)
    finally:
        db.rollback()
        db.query(Chunk).filter(Chunk.tenant_id == tenant_row.id).delete()
        db.query(Document).filter(Document.tenant_id == tenant_row.id).delete()
        db.query(Tenant).filter(Tenant.id == tenant_row.id).delete()
        db.commit()


def eval_followups(db, tenant_id: str, embeddings, k: int):
    """Retrieval for ambiguous follow-ups ("How long does it take?") under four ways of building the search"""
    followups = [json.loads(line) for line in (HERE / "followups.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    llm = RAGPipeline().llm_provider
    retriever = Retriever(embeddings)  # hybrid + rerank, as in production
    # no timeout here: the eval measures the rewrite itself, not how fast the free tier is today
    rewrites = [rewrite_query(llm, f["question"], f["history"], timeout=None) for f in followups]
    for f, r in zip(followups, rewrites):
        print(f"  rewrite: {f['question']!r} -> {r!r}")
    setups = [
        ("as asked (no rewriting)", lambda f, r: retriever.retrieve(db, tenant_id, f["question"], top_k=k)),
        ("previous question + follow-up (fallback, no LLM)", lambda f, r: retriever.retrieve(
            db, tenant_id, fallback_query(f["question"], f["history"]), top_k=k, extra_queries=[f["question"]])),
        ("LLM rewrite (production)", lambda f, r: retriever.retrieve(db, tenant_id, r, top_k=k, extra_queries=[f["question"]])),
    ]
    rows = []
    for name, search in setups:
        ranks = [first_hit_rank(search(f, r), f["evidence"]) for f, r in zip(followups, rewrites)]
        recall = lambda n: sum(1 for x in ranks if x and x <= n) / len(ranks)
        mrr = sum(1 / x for x in ranks if x) / len(ranks)
        rows.append((name, recall(1), recall(3), recall(k), mrr))
        print(f"follow-ups, {name}: recall@1={recall(1):.3f} recall@{k}={recall(k):.3f} mrr={mrr:.3f}")
    return len(followups), rows


def write_report(rows, faithfulness, answered, k, n_questions, n_chunks, backend, followup_rows=None):
    lines = [
        "# RAG evaluation results", "",
        f"{date.today()} · {n_questions} questions · {n_chunks} chunks from eval/corpus · backend: {backend}", "",
        f"| Retrieval | Recall@1 | Recall@3 | Recall@{k} | MRR |", "|---|---|---|---|---|",
        *[f"| {name} | {r1:.3f} | {r3:.3f} | {rk:.3f} | {mrr:.3f} |" for name, r1, r3, rk, mrr in rows],
    ]
    if faithfulness is not None:
        lines += ["", "| Generation (hybrid + rerank) | Score |", "|---|---|",
                  f"| Faithfulness (LLM judge, supported claims / claims) | {faithfulness:.3f} |",
                  f"| Answered (not \"I don't know\") | {answered:.3f} |"]
    if followup_rows is not None:
        n_followups, frows = followup_rows
        lines += ["", f"Follow-up questions ({n_followups} two-turn conversations, e.g. \"How long does it take?\" after asking about repairs), hybrid + rerank:", "",
                  f"| Search query | Recall@1 | Recall@3 | Recall@{k} | MRR |", "|---|---|---|---|---|",
                  *[f"| {name} | {r1:.3f} | {r3:.3f} | {rk:.3f} | {mrr:.3f} |" for name, r1, r3, rk, mrr in frows]]
    lines += ["", "Recall@k: share of questions whose evidence sentence is in a top-k chunk. "
              "MRR: mean of 1/rank of the first such chunk.", ""]
    (HERE / "results.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
