from sqlalchemy.orm import Session
from app.services.llm_provider import LLMProvider
from app.services.embedding_service import EmbeddingService
from app.services.retriever import Retriever
from app.services.query_rewriter import rewrite_query
from app.config import settings
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.llm_provider = LLMProvider()
        self.retriever = Retriever(self.embedding_service)
    
    def answer_question(self, db: Session, tenant_id: str, question: str, document_ids=None, history: Optional[List[Dict]] = None) -> Dict:
        """Process a question through the full RAG pipeline, searching only `document_ids` when given"""
        try:
            result = self.retrieve(db, tenant_id, question, document_ids, history)
            if "context" in result:
                result["answer"] = self.llm_provider.generate_answer(result["search_query"] or question, result.pop("context"))
            return result
        except Exception as e:
            logger.error(f"RAG pipeline error for tenant {tenant_id}: {e}", exc_info=True)
            return {
                "answer": "I encountered an error processing your question. Please try again.",
                "citations": [],
                "confidence": 0.0,
                "fallback": True
            }
    
    def rewrite(self, question: str, history: Optional[List[Dict]]) -> str:
        """The standalone search query for `question` (see QUERY_REWRITE); `history` is earlier {question, answer} turns"""
        mode = settings.QUERY_REWRITE
        if mode == "always" or (mode == "followups" and history):
            return rewrite_query(self.llm_provider, question, history or [])
        return question

    def retrieve(self, db: Session, tenant_id: str, question: str, document_ids=None, history: Optional[List[Dict]] = None) -> Dict:
        """Find the context for a question. Returns `context` to answer from, or a final fallback `answer`.

        Always includes `search_query`: the rewritten standalone question, or None when it was searched as asked.
        """
        search_query = self.rewrite(question, history)
        result = self._retrieve(db, tenant_id, search_query, question, document_ids)
        result["search_query"] = search_query if search_query != question else None
        return result

    def _retrieve(self, db: Session, tenant_id: str, search_query: str, question: str, document_ids) -> Dict:
        # The original wording is searched too, so a poor rewrite can't hide what the user actually asked for
        similarities = self.retriever.retrieve(db, tenant_id, search_query, top_k=5, document_ids=document_ids, extra_queries=[question])

        if not similarities:
            return {
                "answer": "No documents you have access to have been uploaded and processed yet.",
                "citations": [],
                "confidence": 0.0,
                "fallback": True
            }

        # Log top similarities for debugging
        logger.info(f"Top similarities: {[(s[1], s[0].chunk_metadata.get('filename', 'unknown')) for s in similarities]}")
        
        # Order comes from the reranker; the cosine threshold still drops off-topic chunks
        top_chunks = [(chunk, sim) for chunk, sim in similarities if sim > self.embedding_service.min_similarity][:3]
        
        if not top_chunks:
            return {
                "answer": "I couldn't find relevant information in your documents.",
                "citations": [],
                "confidence": 0.0,
                "fallback": True
            }
        
        # Cite only the chunks the LLM actually sees (deduplicated per document)
        seen_docs = set()
        citations = []
        for chunk, sim in top_chunks:
            metadata = chunk.chunk_metadata or {}
            doc_id = metadata.get('document_id', 'unknown')
            if doc_id not in seen_docs:
                seen_docs.add(doc_id)
                citations.append({
                    "document_id": doc_id,
                    "document_name": metadata.get('filename', 'Unknown Document'),
                    "section": metadata.get('section', ''),
                    "page": metadata.get('page', 1),
                    "similarity": sim
                })
        
        return {
            "context": [chunk.content for chunk, _ in top_chunks],
            "citations": citations,
            "confidence": max(sim for _, sim in top_chunks),
            "fallback": False
        }
