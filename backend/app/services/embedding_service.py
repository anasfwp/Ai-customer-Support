from openai import OpenAI
import google.generativeai as genai
from app.config import settings
from typing import List

class EmbeddingService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        
        if self.provider == "openai":
            if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_openai_key_here":
                raise ValueError("OpenAI API key not configured or still using placeholder")
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = "text-embedding-3-small"
        elif self.provider == "gemini":
            if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_key_here":
                raise ValueError("Gemini API key not configured or still using placeholder")
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.client = genai
            self.model = "models/embedding-001"
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
            for text in texts:
                if not text.strip():
                    embeddings.append([0.0] * 768)
                    continue
                result = self.client.embed_content(
                    model=self.model,
                    content=text
                )
                embeddings.append(result['embedding'])
            return embeddings
        
        else:
            raise ValueError(f"Embeddings not supported for provider: {self.provider}")