from sqlalchemy.orm import Session
from sqlalchemy import Text, cast, func
from app.db.models.chunk import Chunk
from app.services.embedding_service import EmbeddingService
from collections import Counter
from functools import lru_cache
from typing import Dict, List, Tuple
import logging
import math
import re
import numpy as np

logger = logging.getLogger(__name__)

CANDIDATES = 20  # taken from each search, fused, then reranked down to top_k

Ranking = List[Tuple[Chunk, float]]  # (chunk, cosine similarity), best first

class Retriever:
    def __init__(self, embedding_service: EmbeddingService, hybrid: bool = True, rerank: bool = True):
        self.embedding_service = embedding_service
        self.hybrid = hybrid
        self.rerank = rerank

    def retrieve(self, db: Session, tenant_id: str, query: str, top_k: int = 5, document_ids=None, extra_queries=()) -> Ranking:
        """Return the top-k (chunk, cosine similarity) pairs: vector + keyword search, fused with RRF, then reranked.

        `document_ids` (ids or a SELECT of them, see app.core.permissions) limits the search to documents the user may see.
        `extra_queries` are searched too and fused in (e.g. the user's original wording next to a rewritten `query`);
        reranking always scores against `query`.
        """
        queries = [query] + [q for q in dict.fromkeys(extra_queries) if q != query]
        search = self._postgres_rankings if db.get_bind().dialect.name == "postgresql" else self._python_rankings
        rankings = []
        for q, embedding in zip(queries, self.embedding_service.embed_texts(queries)):
            rankings += search(db, tenant_id, q, embedding, document_ids)
        candidates = reciprocal_rank_fusion(rankings)[:CANDIDATES]
        if self.rerank:
            candidates = rerank(query, candidates)
        return candidates[:top_k]

    def _postgres_rankings(self, db: Session, tenant_id: str, query: str, query_embedding: List[float], document_ids) -> List[Ranking]:
        distance = Chunk.embedding.cosine_distance(query_embedding)
        base = _visible(db.query(Chunk, distance).filter(Chunk.tenant_id == tenant_id, Chunk.embedding.isnot(None)), document_ids)
        rankings = [base.order_by(distance).limit(CANDIDATES).all()]
        if self.hybrid:
            # Must match the GIN index expression created on startup
            tsv = func.to_tsvector("english", Chunk.content)
            # plainto_tsquery ANDs every word, so one missing word hides a chunk; OR them and let ts_rank order
            tsq = func.to_tsquery("english", func.replace(cast(func.plainto_tsquery("english", query), Text), "&", "|"))
            rankings.append(base.filter(tsv.op("@@")(tsq)).order_by(func.ts_rank_cd(tsv, tsq).desc()).limit(CANDIDATES).all())
        return [[(chunk, 1.0 - float(dist)) for chunk, dist in ranking] for ranking in rankings]

    def _python_rankings(self, db: Session, tenant_id: str, query: str, query_embedding: List[float], document_ids) -> List[Ranking]:
        # shortcut: loads every tenant chunk into memory, only for local SQLite dev; run Postgres locally to drop this
        q = np.array(query_embedding)
        scored = []
        for chunk in _visible(db.query(Chunk).filter(Chunk.tenant_id == tenant_id, Chunk.embedding.isnot(None)), document_ids).all():
            c = np.array(chunk.embedding)
            norm = np.linalg.norm(q) * np.linalg.norm(c)
            if norm > 0:
                scored.append((chunk, float(np.dot(q, c) / norm)))
        rankings = [sorted(scored, key=lambda x: x[1], reverse=True)[:CANDIDATES]]
        if self.hybrid:
            keyword = sorted(zip(scored, bm25(query, [chunk.content for chunk, _ in scored])), key=lambda x: x[1], reverse=True)
            rankings.append([pair for pair, score in keyword if score > 0][:CANDIDATES])
        return rankings


def _visible(query, document_ids):
    return query if document_ids is None else query.filter(Chunk.document_id.in_(document_ids))


def reciprocal_rank_fusion(rankings: List[Ranking], k: int = 60) -> Ranking:
    """Merge rankings by summing 1/(k + rank); rewards chunks that rank well in several lists. Keeps each chunk's best similarity"""
    scores: Dict[str, float] = {}
    pairs: Dict[str, Tuple[Chunk, float]] = {}
    for ranking in rankings:
        for rank, (chunk, sim) in enumerate(ranking):
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (k + rank + 1)
            if chunk.id not in pairs or sim > pairs[chunk.id][1]:
                pairs[chunk.id] = (chunk, sim)
    return [pairs[chunk_id] for chunk_id in sorted(scores, key=scores.get, reverse=True)]


def bm25(query: str, docs: List[str], k1: float = 1.5, b: float = 0.75) -> List[float]:
    tokenized = [re.findall(r"\w+", doc.lower()) for doc in docs]
    if not tokenized:
        return []
    avgdl = sum(map(len, tokenized)) / len(tokenized) or 1.0
    doc_sets = [set(doc) for doc in tokenized]
    terms = set(re.findall(r"\w+", query.lower()))
    idf = {t: math.log(1 + (len(docs) - (df := sum(t in s for s in doc_sets)) + 0.5) / (df + 0.5)) for t in terms}
    scores = []
    for doc in tokenized:
        tf = Counter(doc)
        scores.append(sum(idf[t] * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(doc) / avgdl)) for t in terms if tf[t]))
    return scores


@lru_cache(maxsize=1)
def _ranker():
    from flashrank import Ranker
    # ~22MB ONNX cross-encoder (no torch), downloaded on first use
    return Ranker(model_name="ms-marco-MiniLM-L-12-v2")


def rerank(query: str, candidates: Ranking) -> Ranking:
    """Reorder candidates by cross-encoder relevance; keeps the fused order if the model can't load"""
    if not candidates:
        return candidates
    try:
        from flashrank import RerankRequest
        passages = [{"id": i, "text": chunk.content} for i, (chunk, _) in enumerate(candidates)]
        results = _ranker().rerank(RerankRequest(query=query, passages=passages))
    except Exception:
        logger.exception("Reranker unavailable, falling back to fused ranking")
        return candidates
    return [candidates[r["id"]] for r in results]
