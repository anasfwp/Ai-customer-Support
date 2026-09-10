from sqlalchemy.orm import Session
from app.services.llm_provider import LLMProvider
from app.services.embedding_service import EmbeddingService
from typing import Dict
import logging
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.llm_provider = LLMProvider()
    
    def answer_question(self, db: Session, tenant_id: str, question: str) -> Dict:
        """Process a question through the full RAG pipeline"""
        try:
            from app.db.models.chunk import Chunk
            
            # Get all chunks for this tenant with embeddings
            chunks = db.query(Chunk).filter(
                Chunk.tenant_id == tenant_id,
                Chunk.embedding.isnot(None)
            ).all()
            
            if not chunks:
                return {
                    "answer": "No documents have been uploaded and processed yet. Please upload a document first.",
                    "citations": [],
                    "confidence": 0.0,
                    "fallback": True
                }
            
            logger.info(f"Found {len(chunks)} chunks for tenant {tenant_id}")
            
            # Generate embedding for the question
            question_embedding = self.embedding_service.embed_texts([question])[0]
            question_vec = np.array(question_embedding)
            
            # Calculate similarities
            similarities = []
            for chunk in chunks:
                if chunk.embedding is not None:
                    chunk_vec = np.array(chunk.embedding)
                    dot_product = np.dot(question_vec, chunk_vec)
                    norm_q = np.linalg.norm(question_vec)
                    norm_c = np.linalg.norm(chunk_vec)
                    if norm_q > 0 and norm_c > 0:
                        sim = dot_product / (norm_q * norm_c)
                        similarities.append((chunk, float(sim)))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Log top similarities for debugging
            logger.info(f"Top similarities: {[(s[1], s[0].chunk_metadata.get('filename', 'unknown')) for s in similarities[:5]]}")
            
            # LOWER THRESHOLD: Use 0.2 instead of 0.5
            top_chunks = []
            for chunk, sim in similarities[:5]:
                if sim > 0.2:  # Lowered threshold
                    top_chunks.append((chunk, sim))
            
            if not top_chunks:
                return {
                    "answer": "I couldn't find relevant information in your documents.",
                    "citations": [],
                    "confidence": 0.0,
                    "fallback": True
                }
            
            # Build context from top chunks (use more chunks)
            context = [chunk.content for chunk, _ in top_chunks[:3]]
            
            # Generate answer using LLM
            answer = self.llm_provider.generate_answer(question, context)
            
            # Build citations (deduplicated)
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
                "answer": answer,
                "citations": citations,
                "confidence": float(top_chunks[0][1] if top_chunks else 0.0),
                "fallback": False
            }
            
        except Exception as e:
            logger.error(f"RAG pipeline error: {e}", exc_info=True)
            return {
                "answer": f"I encountered an error processing your question: {str(e)}",
                "citations": [],
                "confidence": 0.0,
                "fallback": True
            }