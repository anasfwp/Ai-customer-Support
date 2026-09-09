from openai import OpenAI
import google.generativeai as genai
from groq import Groq
from app.config import settings
from typing import List

class LLMProvider:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        
        if self.provider == "openai":
            if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_openai_key_here":
                raise ValueError("OpenAI API key not configured or still using placeholder")
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = "gpt-4o-mini"
        elif self.provider == "gemini":
            if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_key_here":
                raise ValueError("Gemini API key not configured or still using placeholder")
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.client = genai
            self.model = "gemini-2.0-flash-exp"
        elif self.provider == "groq":
            if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_groq_key_here":
                raise ValueError("Groq API key not configured or still using placeholder")
            self.client = Groq(api_key=settings.GROQ_API_KEY)
            self.model = "llama-3.3-70b-versatile"
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def generate_answer(self, question: str, context: List[str]) -> str:
        if not context:
            return "I couldn't find relevant information in the documentation."
        
        prompt = self._build_prompt(question, context)
        
        if self.provider == "openai":
            return self._openai_generate(prompt)
        elif self.provider == "gemini":
            return self._gemini_generate(prompt)
        elif self.provider == "groq":
            return self._groq_generate(prompt)
        else:
            return "No valid LLM provider configured."
    
    def _openai_generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Answer based ONLY on the provided context. If you cannot answer from the context, say I dont know."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    
    def _gemini_generate(self, prompt: str) -> str:
        model = self.client.GenerativeModel(self.model)
        response = model.generate_content(prompt)
        return response.text
    
    def _groq_generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Answer based ONLY on the provided context. If you cannot answer from the context, say I dont know."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    
    def _build_prompt(self, question: str, context: List[str]) -> str:
        context_text = "\n\n---\n\n".join(context)
        return f"""Context information:
{context_text}

Question: {question}

Based ONLY on the context above, provide a clear answer. If the answer is not in the context, say I dont know."""