from openai import OpenAI
import google.generativeai as genai
from groq import Groq
from app.config import settings
from typing import Iterator, List

SYSTEM_PROMPT = "You are a helpful assistant. Answer based ONLY on the provided context. If you cannot answer from the context, say I dont know."

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
        return "".join(self.stream_answer(question, context))
    
    def stream_answer(self, question: str, context: List[str]) -> Iterator[str]:
        if not context:
            yield "I couldn't find relevant information in the documentation."
            return
        yield from self.stream(self._build_prompt(question, context))
    
    def stream(self, prompt: str, system: str = SYSTEM_PROMPT) -> Iterator[str]:
        """Yield the completion for `prompt` as it is generated"""
        if self.provider == "gemini":
            model = self.client.GenerativeModel(self.model)
            for chunk in model.generate_content(f"{system}\n\n{prompt}", stream=True):
                yield chunk.text
        else:  # openai and groq share the chat-completions API
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                stream=True
            )
            for event in stream:
                if event.choices and event.choices[0].delta.content:
                    yield event.choices[0].delta.content
    
    def _build_prompt(self, question: str, context: List[str]) -> str:
        context_text = "\n\n---\n\n".join(context)
        return f"""Context information:
{context_text}

Question: {question}

Based ONLY on the context above, provide a clear answer. If the answer is not in the context, say I dont know."""