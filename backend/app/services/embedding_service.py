from openai import OpenAI
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from app.config import settings
from typing import List
import logging
import time

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 1536  # must match Chunk.embedding = Vector(1536)
GEMINI_BATCH = 100  # embedContent batch limit
GEMINI_RETRIES = 3  # free tier allows 100 texts/minute, so a big upload waits out the window

class EmbeddingService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        
        if self.provider == "openai":
            if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_openai_key_here":
                raise ValueError("OpenAI API key not configured or still using placeholder")
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = "text-embedding-3-small"
            self.min_similarity = 0.2  # below this a chunk is treated as off-topic
        elif self.provider == "gemini":
            if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_key_here":
                raise ValueError("Gemini API key not configured or still using placeholder")
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.client = genai
            self.model = "models/gemini-embedding-001"
            # gemini scores unrelated text higher; 0.5 kept all 70 eval questions and rejected 13/18 off-topic ones
            self.min_similarity = 0.5
        elif self.provider == "groq":
            # Groq doesn't have embeddings API, fallback to OpenAI or Gemini
            raise ValueError("Groq does not support embeddings. Please use OpenAI or Gemini for embeddings.")
        else:
            raise ValueError(f"Embeddings not supported for provider: {self.provider}")
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for list of texts"""
        if not texts:
            return []
        
        if self.provider == "openai":
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [data.embedding for data in response.data]
        
        elif self.provider == "gemini":
            embeddings = []
            for i in range(0, len(texts), GEMINI_BATCH):
                batch = texts[i:i + GEMINI_BATCH]
                # the API rejects empty strings; embed a placeholder so positions stay aligned
                for attempt in range(GEMINI_RETRIES + 1):
                    try:
                        result = self.client.embed_content(
                            model=self.model,
                            content=[text if text.strip() else " - " for text in batch],
                            output_dimensionality=EMBEDDING_DIM
                        )
                        break
                    except ResourceExhausted:
                        if attempt == GEMINI_RETRIES:
                            raise
                        logger.warning("Gemini embedding quota hit, retrying in 30s (%d/%d)", attempt + 1, GEMINI_RETRIES)
                        time.sleep(30)
                embeddings.extend(result['embedding'])
            return embeddings
        
        else:
            raise ValueError(f"Embeddings not supported for provider: {self.provider}")